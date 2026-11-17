#ifndef SWITCH_HASH_H
#define SWITCH_HASH_H

#include <unordered_map>
#include <ns3/node.h>
#include "qbb-net-device.h"
#include "switch-mmu.h"
#include "pint.h"

namespace ns3 {

static uint32_t MurmurHash3(const uint8_t* key, size_t len, uint32_t seed) {

  uint32_t h = seed;
  if (len > 3) {
    const uint32_t* key_x4 = (const uint32_t*) key;
    size_t i = len >> 2;
    do {
      uint32_t k = *key_x4++;
      k *= 0xcc9e2d51;
      k = (k << 15) | (k >> 17);
      k *= 0x1b873593;
      h ^= k;
      h = (h << 13) | (h >> 19);
      h += (h << 2) + 0xe6546b64;
    } while (--i);
    key = (const uint8_t*) key_x4;
  }
  if (len & 3) {
    size_t i = len & 3;
    uint32_t k = 0;
    key = &key[i - 1];
    do {
      k <<= 8;
      k |= *key--;
    } while (--i);
    k *= 0xcc9e2d51;
    k = (k << 15) | (k >> 17);
    k *= 0x1b873593;
    h ^= k;
  }
  h ^= len;
  h ^= h >> 16;
  h *= 0x85ebca6b;
  h ^= h >> 13;
  h *= 0xc2b2ae35;
  h ^= h >> 16;
  return h;
}

static uint32_t Crc32Hash(const uint8_t* key, size_t length) {
    static uint32_t table[256];
    static bool initialized = false;

    if (!initialized) {
        // initial CRC table (0xEDB88320) 
        for (uint32_t i = 0; i < 256; ++i) {
            uint32_t crc = i;
            for (int j = 0; j < 8; ++j)
                crc = (crc >> 1) ^ (0xEDB88320U & (-(int)(crc & 1)));
            table[i] = crc;
        }
        initialized = true;
    }

    uint32_t crc = 0xFFFFFFFFU;
    for (size_t i = 0; i < length; ++i)
        crc = (crc >> 8) ^ table[(crc ^ key[i]) & 0xFF];

    return crc ^ 0xFFFFFFFFU;
}

static uint32_t JenkinsHash(const uint8_t* key, size_t length) {
    uint32_t hash = 0;
    for (size_t i = 0; i < length; ++i) {
        hash += key[i];
        hash += (hash << 10);
        hash ^= (hash >> 6);
    }
    hash += (hash << 3);
    hash ^= (hash >> 11);
    hash += (hash << 15);
    return hash;
}


static uint32_t SymHash(const uint8_t* key, size_t length, uint32_t seed) {
	// get ip
	const uint32_t sip = *(const uint32_t*) key;
	const uint32_t dip = *(const uint32_t*) (key + 4); 

	// get port
	uint16_t sport = *(uint16_t*) (key + 8);
	uint16_t dport = *(uint16_t*) (key + 10);

  uint32_t ip_min = std::min(sip, dip);
  uint32_t ip_max = std::max(sip, dip);

  uint32_t port_min = std::min<uint16_t>(sport, dport);
  uint32_t port_max = std::max<uint16_t>(sport, dport);

  uint32_t h = seed;

  h ^= ip_min + 0x9e3779b9 + (h << 6) + (h >> 2);
  h ^= ip_max + 0x9e3779b9 + (h << 6) + (h >> 2);
  h ^= ((port_max << 16) | port_min) + 0x9e3779b9 + (h << 6) + (h >> 2);

  h ^= (h >> 16);
  h *= 0x85ebca6b;
  h ^= (h >> 13);
  h *= 0xc2b2ae35;
  h ^= (h >> 16);

  return h;
}

static uint32_t FlowBenderHash(const uint8_t* key, size_t len, uint32_t seed, uint32_t ttl) {
  uint32_t h = seed ^ ttl;
  if (len > 3) {
    const uint32_t* key_x4 = (const uint32_t*) key;
    size_t i = len >> 2;
    do {
      uint32_t k = *key_x4++;
      k *= 0xcc9e2d51;
      k = (k << 15) | (k >> 17);
      k *= 0x1b873593;
      h ^= k;
      h = (h << 13) | (h >> 19);
      h += (h << 2) + 0xe6546b64;
    } while (--i);
    key = (const uint8_t*) key_x4;
  }
  if (len & 3) {
    size_t i = len & 3;
    uint32_t k = 0;
    key = &key[i - 1];
    do {
      k <<= 8;
      k |= *key--;
    } while (--i);
    k *= 0xcc9e2d51;
    k = (k << 15) | (k >> 17);
    k *= 0x1b873593;
    h ^= k;
  }
  h ^= len;
  h ^= h >> 16;
  h *= 0x85ebca6b;
  h ^= h >> 13;
  h *= 0xc2b2ae35;
  h ^= h >> 16;
  return h;
}

}


#endif /* SWITCH_HASH_H */
