"""CLI and graph checks for Spectrum-X multi-plane topology generation.

Run with: python3 -m unittest discover -s astra-sim-alibabacloud/inputs/topo \
    -p 'test_spectrum_multiplane.py'
"""

from collections import defaultdict
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


GENERATOR = Path(__file__).with_name("gen_Topo_Template.py")


class SpectrumMultiPlaneTests(unittest.TestCase):
    def invoke(self, args):
        """Keep all generated topologies and metadata outside the repository."""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(GENERATOR), *args],
                cwd=directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
            files = {
                path.name: path.read_bytes()
                for path in Path(directory).iterdir()
                if path.is_file()
            }
        return result, files

    def spectrum_args(self, gpu=32, gps=8, npa=4, psw=4, nsps=1, app=64):
        return [
            "-topo", "Spectrum-X", "-g", str(gpu), "-gps", str(gps),
            "-npa", str(npa), "-psn", str(psw), "-nsps", str(nsps),
            "-app", str(app), "-gt", "A100",
            "-bw", "200Gbps", "-apbw", "400Gbps",
        ]

    def assert_multiplane_graph(self, gpu, gps, npa, psw, nsps, planes):
        result, files = self.invoke(
            self.spectrum_args(gpu, gps, npa, psw, nsps) + ["--planes", str(planes)]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        name = f"Spectrum-X_{gpu}g_{gps}gps_{planes}planes_200Gbps_A100"
        self.assertIn(name, files)
        lines = files[name].decode().splitlines()
        header = lines[0].split()
        self.assertEqual(len(header), 6)
        nodes, file_gps, nv_count, switch_count, link_count = map(int, header[:5])
        leaf_count = ((gpu // gps + npa - 1) // npa) * gps
        expected_nv = gpu // gps * nsps
        self.assertEqual(file_gps, gps)
        self.assertEqual(header[5], "A100")
        self.assertEqual(nv_count, expected_nv)
        self.assertEqual(switch_count, planes * (leaf_count + psw))
        self.assertEqual(nodes, gpu + expected_nv + switch_count)
        self.assertEqual(link_count, gpu * nsps + planes * (gpu + leaf_count * psw))

        switch_ids = list(map(int, lines[1].split()))
        self.assertEqual(len(switch_ids), nv_count + switch_count)
        self.assertEqual(len(set(switch_ids)), len(switch_ids))
        self.assertEqual(set(switch_ids), set(range(gpu, nodes)))
        nv_ids = set(switch_ids[:nv_count])
        network_ids = set(switch_ids[nv_count:])
        self.assertEqual(nv_ids, set(range(gpu, gpu + nv_count)))

        adjacency = defaultdict(set)
        seen_edges = set()
        self.assertEqual(len(lines[2:]), link_count)
        for line in lines[2:]:
            fields = line.split()
            self.assertEqual(len(fields), 5, line)
            src, dst = map(int, fields[:2])
            self.assertTrue(0 <= src < nodes and 0 <= dst < nodes, line)
            self.assertNotEqual(src, dst)
            edge = tuple(sorted((src, dst)))
            self.assertNotIn(edge, seen_edges, line)
            seen_edges.add(edge)
            adjacency[src].add(dst)
            adjacency[dst].add(src)
            self.assertEqual(float(fields[4]), 0)
            if src in nv_ids or dst in nv_ids:
                self.assertEqual(fields[2:4], ["2880Gbps", "0.000025ms"])
            elif src < gpu or dst < gpu:
                self.assertEqual(fields[2:4], ["200Gbps", "0.0005ms"])
            else:
                self.assertEqual(fields[2:4], ["400Gbps", "0.0005ms"])

        # Sharing hosts must not merge the independent switch fabrics.
        remaining = set(network_ids)
        fabrics = []
        while remaining:
            start = remaining.pop()
            component = {start}
            pending = [start]
            while pending:
                current = pending.pop()
                for neighbor in adjacency[current] & remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
            fabrics.append(component)
        self.assertEqual(len(fabrics), planes)

        for fabric in fabrics:
            leaves = {node for node in fabric if any(peer < gpu for peer in adjacency[node])}
            spines = fabric - leaves
            self.assertEqual(len(leaves), leaf_count)
            self.assertEqual(len(spines), psw)
            for leaf in leaves:
                self.assertEqual(adjacency[leaf] & network_ids, spines)
            for spine in spines:
                self.assertEqual(adjacency[spine], leaves)

            # All servers in a segment use the same Leaf for a given GPU rail.
            rails = {}
            for gpu_id in range(gpu):
                attached = adjacency[gpu_id] & fabric
                self.assertEqual(len(attached), 1)
                leaf = next(iter(attached))
                self.assertIn(leaf, leaves)
                rail_key = ((gpu_id // gps) // npa, gpu_id % gps)
                if rail_key in rails:
                    self.assertEqual(rails[rail_key], leaf)
                else:
                    rails[rail_key] = leaf
            self.assertEqual(len(set(rails.values())), leaf_count)

        for gpu_id in range(gpu):
            server = gpu_id // gps
            expected_nv_ids = set(range(gpu + server * nsps, gpu + (server + 1) * nsps))
            self.assertEqual(adjacency[gpu_id] & nv_ids, expected_nv_ids)
            self.assertEqual(len(adjacency[gpu_id]), nsps + planes)
        for nv_id in nv_ids:
            server = (nv_id - gpu) // nsps
            self.assertEqual(adjacency[nv_id], set(range(server * gps, (server + 1) * gps)))

    def test_two_planes(self):
        self.assert_multiplane_graph(gpu=32, gps=8, npa=4, psw=4, nsps=1, planes=2)

    def test_three_planes_partial_segment_multiple_nvswitches(self):
        self.assert_multiplane_graph(gpu=40, gps=8, npa=4, psw=3, nsps=2, planes=3)

    def test_single_plane_preserves_default_file_bytes(self):
        result, files = self.invoke(self.spectrum_args())
        explicit, explicit_files = self.invoke(self.spectrum_args() + ["--planes", "1"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        self.assertIn("Spectrum-X_32g_8gps_200Gbps_A100", files)
        self.assertEqual(files, explicit_files)

    def test_invalid_multiplane_parameters_rejected_before_writing(self):
        invalid = [
            ["--planes", "0"], ["--planes", "-1"], ["--planes", "1.5"],
            ["--planes", "2", "--dp"], ["--planes", "2", "--dt"],
            ["--planes", "2", "-g", "33"],
            ["--planes", "2", "-g", "0"],
            ["--planes", "2", "-gps", "0"],
            ["--planes", "2", "-npa", "0"],
            ["--planes", "2", "-psn", "0"],
            ["--planes", "2", "-nsps", "0"],
            ["--planes", "2", "-app", "0"],
            ["--planes", "2", "-app", "7"],
        ]
        for extra in invalid:
            with self.subTest(extra=extra):
                result, files = self.invoke(self.spectrum_args() + extra)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(files, {})

    def test_planes_option_rejected_for_other_templates(self):
        for template in ["AlibabaHPN", "DCN+", "Fat_tree"]:
            for planes in ["1", "2"]:
                with self.subTest(template=template, planes=planes):
                    result, files = self.invoke(["-topo", template, "--planes", planes])
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(files, {})

    def test_hpn_dual_plane_remains_available(self):
        result, files = self.invoke([
            "-topo", "AlibabaHPN", "--dp", "-g", "32", "-gps", "8",
            "-npa", "4", "-psn", "8", "-app", "16", "-gt", "A100",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        name = "AlibabaHPN_32g_8gps_DualToR_DualPlane_200Gbps_A100"
        self.assertIn(name, files)
        lines = files[name].decode().splitlines()
        self.assertEqual(int(lines[0].split()[4]), len(lines) - 2)


if __name__ == "__main__":
    unittest.main()
