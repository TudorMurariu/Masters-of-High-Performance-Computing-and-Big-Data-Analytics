#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
#include <vector>
#include <thread>
#include <mutex>
using namespace std;

const string INPUT_FILE_NAME = "input.txt";

uint32_t M, N;
string FileA, FileB, FileC;

void read_M() {
    ifstream rf(INPUT_FILE_NAME);

    if (rf.fail()) {
        cout << "Cannot open input file!" << endl;
        return;
    }

    rf >> M >> FileA >> FileB >> FileC;
}

double fRand(double fMin = 0, double fMax = 10)
{
    double f = (double)rand() / RAND_MAX;
    return fMin + f * (fMax - fMin);
}

double** generate_random_matrix(uint32_t M)
{
    double** mat = new double* [M];

    for (uint32_t i = 0; i < M; ++i)
    {
        mat[i] = new double[M];
        for (uint32_t j = 0; j < M; ++j)
            mat[i][j] = fRand();
    }

    return mat;
}

void write(uint32_t M, double** mat, string fileName) {
    ofstream wf(fileName);

    if (wf.fail()) {
        cout << "Cannot open file!" << endl;
        return;
    }

    for (uint32_t i = 0; i < M; ++i)
    {
        for (uint32_t j = 0; j < M; ++j)
            wf << mat[i][j] << " ";
        wf << "\n";
    }
}

void write_binary(uint32_t M, double** mat, string fileName) {
    ofstream wf(fileName, ios::out | ios::binary);

    if (wf.fail()) {
        cout << "Cannot open file!" << endl;
        return;
    }

    for (uint32_t i = 0; i < M; ++i)
    {
        for (uint32_t j = 0; j < M; ++j)
        {
            wf.write(reinterpret_cast<char*>(&mat[i][j]), sizeof(double));
        }
    }
}

double** read_mat(uint32_t M, string fileName) {
    ifstream rf(fileName);

    double** mat = new double* [M];

    for (uint32_t i = 0; i < M; ++i)
    {
        mat[i] = new double[M];
        for (uint32_t j = 0; j < M; ++j)
            rf >> mat[i][j];
    }

    return mat;
}

double** read_binary_parallel(uint32_t M, string fileName, uint32_t N) {
    ifstream rf(fileName, ios::in | ios::binary);
    if (!rf) {
        cerr << "Error opening file: " << fileName << endl;
        return nullptr;
    }

    double** mat = new double* [M];
    for (uint32_t i = 0; i < M; ++i)
        mat[i] = new double[M];

    auto read_chunk = [&](uint32_t start_row, uint32_t end_row) {
        ifstream thread_rf(fileName, ios::in | ios::binary);
        if (!thread_rf) return;

        thread_rf.seekg(start_row * M * sizeof(double), ios::beg);
        for (uint32_t i = start_row; i < end_row; ++i) {
            thread_rf.read(reinterpret_cast<char*>(mat[i]), M * sizeof(double));
        }
        };

    vector<thread> threads;
    uint32_t rows_per_thread = M / N;
    uint32_t extra_rows = M % N;

    uint32_t start_row = 0;
    for (uint32_t i = 0; i < N; ++i) {
        uint32_t end_row = start_row + rows_per_thread + (i < extra_rows ? 1 : 0);
        threads.emplace_back(read_chunk, start_row, end_row);
        start_row = end_row;
    }

    for (auto& t : threads) t.join();

    return mat;
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
    auto r_start = chrono::steady_clock::now();
    auto t_start = r_start;

    read_M();
    cout << M << " " << FileA << " " << FileB << " " << FileC << endl;

    double** A = read_binary_parallel(M, FileA, N);
    double** B = read_binary_parallel(M, FileB, N);

    auto r_final = chrono::steady_clock::now();
    auto diff = r_final - r_start;
    cout << "computation time of the main thread FOR READ = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;
    fout << "computation time of the main thread FOR READ = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;


    auto c_start = chrono::steady_clock::now();

    double** C = product_of_matrix(M, A, B, N);

    auto c_final = chrono::steady_clock::now();
    diff = c_final - c_start;
    cout << "computation time of the main thread FOR COMPUTATION = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;
    fout << "computation time of the main thread FOR COMPUTATION = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;


    auto w_start = chrono::steady_clock::now();
    write_binary(M, C, FileC);

    auto w_final = chrono::steady_clock::now();
    diff = w_final - w_start;
    cout << "computation time of the main thread FOR WRITE = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;
    fout << "computation time of the main thread FOR WRITE = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;

    auto t_final = chrono::steady_clock::now();
    diff = t_final - t_start;
    cout << "computation time of the main thread FOR TOTAL EXEC = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;
    fout << "computation time of the main thread FOR TOTAL EXEC = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;

    return 0;
}