#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
using namespace std;

double fRand(double fMin = 0, double fMax = 10)
{
    double f = (double)rand() / RAND_MAX;
    return fMin + f * (fMax - fMin);
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
            double x = fRand();
            wf.write(reinterpret_cast<char*>(&x, sizeof(double));
        }
    }
}

int main()
{
    // generate matrixes
    int M = 10000;
    double** A = generate_random_matrix(M);
    write_binary(M, A, "A.bin");

    double** B = generate_random_matrix(M);
    write_binary(M, B, "B.bin");

    return 0;
}
