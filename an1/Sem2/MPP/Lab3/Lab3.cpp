#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <omp.h>

using namespace std;
using namespace std::chrono;

void read_input(const string& input_file, int& M, string& fileA, string& fileB, string& fileC) {
    ifstream fin(input_file);
    if (!fin) {
        cerr << "Failed to open input.txt\n";
        exit(1);
    }
    fin >> M >> fileA >> fileB >> fileC;
    fin.close();
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <num_threads>\n";
        return 1;
    }

    int num_threads = stoi(argv[1]);
    omp_set_num_threads(num_threads);

    int M;
    string fileA, fileB, fileC;
    read_input("input.txt", M, fileA, fileB, fileC);
    cout << "Matrix size: " << M << " Nr of threads: " << num_threads << endl;

    // Initialize matrices A, B, and C
    vector<double> A(M * M), B(M * M), C(M * M, 0.0);

    auto start_total = steady_clock::now();

    // Reading matrices from binary files
    auto r_start = steady_clock::now();
    ifstream fa(fileA, ios::binary);
    ifstream fb(fileB, ios::binary);
    fa.read(reinterpret_cast<char*>(A.data()), M * M * sizeof(double));
    fb.read(reinterpret_cast<char*>(B.data()), M * M * sizeof(double));
    fa.close(); fb.close();
    auto r_final = steady_clock::now();
    cout << "Read time: " << duration<double, milli>(r_final - r_start).count() << " ms" << endl;

    // Matrix multiplication (parallel)
    auto m_start = steady_clock::now();
#pragma omp parallel for collapse(2)
    for (int i = 0; i < M; ++i) {
        for (int j = 0; j < M; ++j) {
            double sum = 0.0;
            for (int k = 0; k < M; ++k) {
                sum += A[i * M + k] * B[k * M + j];
            }
            C[i * M + j] = sum;
        }
    }
    auto m_final = steady_clock::now();
    cout << "Matrix multiplication time: " << duration<double, milli>(m_final - m_start).count() << " ms" << endl;

    // Writing the result matrix C to a binary file
    auto w_start = steady_clock::now();
    ofstream fc(fileC, ios::binary);
    fc.write(reinterpret_cast<char*>(C.data()), M * M * sizeof(double));
    fc.close();
    auto w_final = steady_clock::now();
    cout << "Write time: " << duration<double, milli>(w_final - w_start).count() << " ms" << endl;

    auto total_final = steady_clock::now();
    cout << "Total execution time: " << duration<double, milli>(total_final - start_total).count() << " ms" << endl;

    return 0;
}
