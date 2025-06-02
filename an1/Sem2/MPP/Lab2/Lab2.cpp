#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
#include <vector>
#include <thread>
#include <mutex>

using namespace std;

const string INPUT_FILE_NAME = "input.txt";

uint32_t M, N;  // M = Matrix size, N = Number of threads
string FileA, FileB, FileC;

void read_M() {
    ifstream rf(INPUT_FILE_NAME);
    if (rf.fail()) {
        cout << "Cannot open input file!" << endl;
        return;
    }
    rf >> M >> FileA >> FileB >> FileC;
}

double** read_binary(uint32_t M, string fileName) {
    ifstream rf(fileName, ios::in | ios::binary);
    double** mat = new double* [M];
    for (uint32_t i = 0; i < M; ++i) {
        mat[i] = new double[M];
        for (uint32_t j = 0; j < M; ++j) {
            rf.read(reinterpret_cast<char*>(&mat[i][j]), sizeof(double));
        }
    }
    return mat;
}

void write_binary(uint32_t M, double** mat, string fileName) {
    ofstream wf(fileName, ios::out | ios::binary);
    if (wf.fail()) {
        cout << "Cannot open file!" << endl;
        return;
    }
    for (uint32_t i = 0; i < M; ++i) {
        for (uint32_t j = 0; j < M; ++j) {
            wf.write(reinterpret_cast<char*>(&mat[i][j]), sizeof(double));
        }
    }
}


void multiply_rows(uint32_t start, uint32_t end, uint32_t M, double** A, double** B, double** C) {
    for (uint32_t i = start; i < end; ++i) {
        for (uint32_t j = 0; j < M; ++j) {
            C[i][j] = 0.0;
            for (uint32_t k = 0; k < M; ++k) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

double** product_of_matrix(uint32_t M, double** A, double** B, uint32_t N) {
    double** C = new double* [M];
    for (uint32_t i = 0; i < M; ++i)
        C[i] = new double[M];

    vector<thread> threads;
    uint32_t rows_per_thread = M / N;
    uint32_t remaining_rows = M % N;

    uint32_t start = 0;
    for (uint32_t i = 0; i < N; ++i) {
        uint32_t end = start + rows_per_thread + (i < remaining_rows ? 1 : 0);
        threads.emplace_back(multiply_rows, start, end, M, A, B, C);
        start = end;
    }

    for (auto& th : threads) {
        th.join();
    }

    return C;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        cout << "Usage: " << argv[0] << " <num_threads>" << endl;
        return 1;
    }

    N = stoi(argv[1]); // Convert command-line argument to integer
    if (N < 1) {
        cout << "Number of threads must be at least 1!" << endl;
        return 1;
    }

    ofstream fout("OUTPUT10k.txt");

    read_M();
    cout << "Matrix Size: " << M << ", Threads: " << N << endl;

    auto r_start = chrono::steady_clock::now();
    double** A = read_binary(M, FileA);
    double** B = read_binary(M, FileB);
    auto r_final = chrono::steady_clock::now();

    cout << "Read time: " << chrono::duration<double, milli>(r_final - r_start).count() << " ms" << endl;

    auto c_start = chrono::steady_clock::now();
    double** C = product_of_matrix(M, A, B, N);
    auto c_final = chrono::steady_clock::now();

    cout << "Computation time: " << chrono::duration<double, milli>(c_final - c_start).count() << " ms" << endl;

    auto w_start = chrono::steady_clock::now();
    write_binary(M, C, FileC);
    auto w_final = chrono::steady_clock::now();

    cout << "Write time: " << chrono::duration<double, milli>(w_final - w_start).count() << " ms" << endl;

    auto t_final = chrono::steady_clock::now();
    cout << "Total execution time: " << chrono::duration<double, milli>(t_final - r_start).count() << " ms" << endl;

    return 0;
}