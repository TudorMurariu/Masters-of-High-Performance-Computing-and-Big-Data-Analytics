#include <cuda_runtime.h>
#include <iostream>
#include <cstdint>
#include <cstring>
#include <chrono>

// ================= SHA1 =================

struct SHA1_CTX {
    uint32_t state[5];
    uint64_t count;
    uint8_t buffer[64];
};

__device__ __host__ uint32_t rotl(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

__device__ __host__ void sha1_transform(uint32_t state[5], const uint8_t buffer[64]) {
    uint32_t a, b, c, d, e, t, W[80];

    for (int i = 0; i < 16; i++)
        W[i] = (buffer[4 * i] << 24) |
        (buffer[4 * i + 1] << 16) |
        (buffer[4 * i + 2] << 8) |
        (buffer[4 * i + 3]);

    for (int i = 16; i < 80; i++)
        W[i] = rotl(W[i - 3] ^ W[i - 8] ^ W[i - 14] ^ W[i - 16], 1);

    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];

    for (int i = 0; i < 80; i++) {
        if (i < 20)
            t = rotl(a, 5) + ((b & c) | (~b & d)) + e + W[i] + 0x5A827999;
        else if (i < 40)
            t = rotl(a, 5) + (b ^ c ^ d) + e + W[i] + 0x6ED9EBA1;
        else if (i < 60)
            t = rotl(a, 5) + ((b & c) | (b & d) | (c & d)) + e + W[i] + 0x8F1BBCDC;
        else
            t = rotl(a, 5) + (b ^ c ^ d) + e + W[i] + 0xCA62C1D6;

        e = d;
        d = c;
        c = rotl(b, 30);
        b = a;
        a = t;
    }

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
}

__device__ __host__ void sha1(const uint8_t* data, size_t len, uint8_t hash[20]) {
    SHA1_CTX ctx{};
    ctx.state[0] = 0x67452301;
    ctx.state[1] = 0xEFCDAB89;
    ctx.state[2] = 0x98BADCFE;
    ctx.state[3] = 0x10325476;
    ctx.state[4] = 0xC3D2E1F0;
    ctx.count = 0;

    size_t i = 0;
    while (len--) {
        ctx.buffer[ctx.count & 63] = data[i++];
        if ((++ctx.count & 63) == 0)
            sha1_transform(ctx.state, ctx.buffer);
    }

    uint64_t bit_len = ctx.count * 8;
    ctx.buffer[ctx.count & 63] = 0x80;

    while ((++ctx.count & 63) != 56)
        ctx.buffer[ctx.count & 63] = 0;

    for (int j = 7; j >= 0; j--)
        ctx.buffer[56 + j] = bit_len >> (8 * (7 - j));

    sha1_transform(ctx.state, ctx.buffer);

    for (i = 0; i < 5; i++) {
        hash[4 * i] = ctx.state[i] >> 24;
        hash[4 * i + 1] = ctx.state[i] >> 16;
        hash[4 * i + 2] = ctx.state[i] >> 8;
        hash[4 * i + 3] = ctx.state[i];
    }
}

// ================= CPU NONCE SEARCH =================

uint32_t find_nonce_cpu(const uint8_t* data, size_t data_len,
    const uint8_t* suffix, int suffix_len) {
    uint8_t buffer[64];
    uint8_t hash[20];
    uint32_t nonce = 0;

    while (true) {
        memcpy(buffer, data, data_len);
        memcpy(buffer + data_len, &nonce, sizeof(nonce));

        sha1(buffer, data_len + sizeof(nonce), hash);

        if (memcmp(hash + 20 - suffix_len, suffix, suffix_len) == 0)
            return nonce;

        nonce++;
    }
}

// ================= GPU KERNEL =================

__global__ void nonce_kernel(const uint8_t* data, size_t data_len,
    const uint8_t* suffix, int suffix_len,
    uint32_t start_nonce,
    uint32_t* result, int* found) {

    // registri
    uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    uint32_t total_threads = gridDim.x * blockDim.x;

    uint8_t buffer[64];
    uint8_t hash[20];

    uint32_t nonce_offset = 0;

    while (!(*found)) {
        uint32_t nonce = start_nonce + idx + nonce_offset * total_threads;

        for (int j = 0; j < data_len; j++)
            buffer[j] = data[j];

        buffer[data_len + 0] = (nonce >> 0) & 0xFF;
        buffer[data_len + 1] = (nonce >> 8) & 0xFF;
        buffer[data_len + 2] = (nonce >> 16) & 0xFF;
        buffer[data_len + 3] = (nonce >> 24) & 0xFF;

        sha1(buffer, data_len + 4, hash);

        bool match = true;
        for (int j = 0; j < suffix_len; j++) {
            if (hash[20 - suffix_len + j] != suffix[j]) {
                match = false;
                break;
            }
        }

        if (match && atomicCAS(found, 0, 1) == 0) {
            *result = nonce;
            return;
        }
        nonce_offset++;
    }
}


uint32_t run_cpu_nonce_search(const uint8_t* data, size_t data_len,
    const uint8_t* suffix, int suffix_len) {
    auto start = std::chrono::high_resolution_clock::now();
    uint32_t nonce = find_nonce_cpu(data, data_len, suffix, suffix_len);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    std::cout << "[CPU] Nonce: " << nonce
        << " | Time: " << elapsed.count() << " s\n";

    return nonce;
}

uint32_t run_gpu_nonce_search(const uint8_t* data, size_t data_len,
    const uint8_t* suffix, int suffix_len) {
    uint8_t* d_data;
    uint8_t* d_suffix;
    uint32_t* d_result;
    int* d_found;

    cudaMalloc(&d_data, data_len);
    cudaMalloc(&d_suffix, suffix_len);
    cudaMalloc(&d_result, sizeof(uint32_t));
    cudaMalloc(&d_found, sizeof(int));

    int zero = 0;
    cudaMemcpy(d_data, data, data_len, cudaMemcpyHostToDevice);
    cudaMemcpy(d_suffix, suffix, suffix_len, cudaMemcpyHostToDevice);
    cudaMemcpy(d_found, &zero, sizeof(int), cudaMemcpyHostToDevice);

    dim3 threads(256);
    dim3 blocks(64); // adjust for more nonces

    auto start = std::chrono::high_resolution_clock::now();
    nonce_kernel << <blocks, threads >> > (d_data, data_len, d_suffix, suffix_len, 0, d_result, d_found);
    cudaDeviceSynchronize();
    auto end = std::chrono::high_resolution_clock::now();

    uint32_t nonce;
    cudaMemcpy(&nonce, d_result, sizeof(uint32_t), cudaMemcpyDeviceToHost);

    std::chrono::duration<double> elapsed = end - start;
    std::cout << "[GPU] Nonce: " << nonce
        << " | Time: " << elapsed.count() << " s\n";

    cudaFree(d_data);
    cudaFree(d_suffix);
    cudaFree(d_result);
    cudaFree(d_found);

    return nonce;
}


// ================= MAIN =================

int main() {
    const uint8_t DATA[] = { 'h','e','l','l','o' };
    const size_t DATA_LEN = sizeof(DATA);

    const uint8_t SUFFIX1[] = { 0x00 };
    const int SUFFIX1_LEN = 1;

    const uint8_t SUFFIX2[] = { 0x12, 0x34 };
    const int SUFFIX2_LEN = 2;

    const uint8_t SUFFIX3[] = { 0x12, 0x34, 0x56 };
    const int SUFFIX_LEN3 = 3;

    const uint8_t SUFFIX4[] = { 0x12, 0x34, 0x56, 0x22 };
    const int SUFFIX_LEN4 = 4;

    std::cout << "--------------------- SUFIX LEN 1\n";

    // Run CPU and GPU on suffix
    run_gpu_nonce_search(DATA, DATA_LEN, SUFFIX1, SUFFIX1_LEN);
    run_cpu_nonce_search(DATA, DATA_LEN, SUFFIX1, SUFFIX1_LEN);

    std::cout << "--------------------- SUFIX LEN 2\n";

    run_gpu_nonce_search(DATA, DATA_LEN, SUFFIX2, SUFFIX2_LEN);
    run_cpu_nonce_search(DATA, DATA_LEN, SUFFIX2, SUFFIX2_LEN);

    std::cout << "--------------------- SUFIX LEN 3\n";

    run_gpu_nonce_search(DATA, DATA_LEN, SUFFIX3, SUFFIX_LEN3);
    run_cpu_nonce_search(DATA, DATA_LEN, SUFFIX3, SUFFIX_LEN3);

    std::cout << "--------------------- SUFIX LEN 4\n";

    run_gpu_nonce_search(DATA, DATA_LEN, SUFFIX4, SUFFIX_LEN4);
    // run_cpu_nonce_search(DATA, DATA_LEN, SUFFIX4, SUFFIX_LEN4);
    // CPU takes too long...

    return 0;
}
