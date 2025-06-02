#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
using namespace std;

const string INPUT_FILE_NAME = "input.txt";

uint32_t M;
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

// Time Complexity: O(M^3)
double** product_of_matrix(uint32_t M, double** A, double** B) {
    double** mat = new double* [M];

    for (uint32_t i = 0; i < M; ++i)
    {
        mat[i] = new double[M];
        for (uint32_t j = 0; j < M; ++j)
        {
            mat[i][j] = 0.0;
            for (uint32_t k = 0; k < M; k++)
                mat[i][j] += A[i][k] * B[k][j];
        }
    }

    return mat;
}

int main()
{
    ofstream fout("OUTPUT10k.txt");
    auto r_start = chrono::steady_clock::now();
    auto t_start = r_start;

    read_M();
    cout << M << " " << FileA << " " << FileB << " " << FileC << endl;

    double** A = read_binary(M, FileA);
    double** B = read_binary(M, FileB);

    auto r_final = chrono::steady_clock::now();
    auto diff = r_final - r_start;
    cout << "computation time of the main thread FOR READ = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;
    fout << "computation time of the main thread FOR READ = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;


    auto c_start = chrono::steady_clock::now();

    double** C = product_of_matrix(M, A, B);

    auto c_final = chrono::steady_clock::now();
    diff = c_final - c_start;
    cout << "computation time of the main thread FOR COMPUTATION = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;
    fout << "computation time of the main thread FOR COMPUTATION = " << chrono::duration <double, milli>(diff).count() << " ms" << endl;


    auto w_start = chrono::steady_clock::now();
    //write(M, C, "output.txt");
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

