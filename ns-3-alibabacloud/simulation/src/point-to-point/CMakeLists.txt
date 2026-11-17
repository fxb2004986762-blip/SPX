set(mpi_sources)
set(mpi_headers)
set(mpi_libraries)

if(${ENABLE_MPI})
  set(mpi_sources
      # model/point-to-point-remote-channel.cc
  )
  set(mpi_headers
      # model/point-to-point-remote-channel.h
  )
  set(mpi_libraries
      # ${libmpi}
      # ${MPI_CXX_LIBRARIES}
  )
endif()

build_lib(
  LIBNAME point-to-point
  SOURCE_FILES
    ${mpi_sources}
    helper/point-to-point-helper.cc
    helper/qbb-helper.cc
    helper/p2p-utils.cc
    model/point-to-point-channel.cc
    model/point-to-point-net-device.cc
    model/ppp-header.cc
    model/qbb-net-device.cc
    model/pause-header.cc
    model/cn-header.cc
    model/pint.cc
    model/qbb-header.cc
    model/qbb-channel.cc
    model/qbb-remote-channel.cc
    model/rdma-driver.cc
    model/rdma-queue-pair.cc
    model/psn-path.cc
    model/rdma-hw.cc
    model/switch-node.cc
    model/switch-mmu.cc
    model/nvswitch-node.cc
    model/point-to-point-remote-channel.cc
    model/letflow-routing.cc
    model/settings.cc
    model/flow-stat-tag.cc
    model/flow-type-tag.cc
    model/flow-info-tag.cc
    model/flow-custom-header-tag.cc
  HEADER_FILES
    ${mpi_headers}
    helper/point-to-point-helper.h
    helper/qbb-helper.h
    helper/sim-setting.h
    model/point-to-point-channel.h
    model/point-to-point-net-device.h
    model/ppp-header.h
    model/qbb-net-device.h
    model/pause-header.h
    model/cn-header.h
    model/pint.h
    model/qbb-header.h
    model/qbb-channel.h
    model/qbb-remote-channel.h
    model/rdma-driver.h
    model/rdma-queue-pair.h
    model/psn-path.h
    model/rdma-hw.h
    model/switch-node.h
    model/switch-mmu.h
    model/trace-format.h
    model/nvswitch-node.h
    model/point-to-point-remote-channel.h
    model/point-to-point-utils.h
    model/letflow-routing.h
    model/settings.h    
    model/switch-hash.h
    model/flow-stat-tag.h
    model/flow-type-tag.h
    model/flow-info-tag.h
    model/flow-custom-header-tag.h
  LIBRARIES_TO_LINK ${libnetwork}
                    ${mpi_libraries}
  TEST_SOURCES
    test/point-to-point-test.cc
    test/psn-path-test.cc
)
