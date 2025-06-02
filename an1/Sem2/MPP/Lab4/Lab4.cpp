#include <mpi.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <chrono>

using namespace std;
using namespace chrono;

const string INPUT_FILE_NAME = "input.txt";

uint32_t M;
string FileA, FileB, FileC;

void read_input() {
    ifstream rf(INPUT_FILE_NAME);
    if (!rf.is_open()) {
        cerr << "Cannot open input file!" << endl;
        exit(1);
    }
    rf >> M >> FileA >> FileB >> FileC;
}

void read_matrix_binary(double* mat, uint32_t M, const string& fileName) {
    ifstream rf(fileName, ios::in | ios::binary);
    if (!rf.is_open()) {
        cerr << "Cannot open matrix file!" << endl;
        exit(1);
    }
    rf.read(reinterpret_cast<char*>(mat), sizeof(double) * M * M);
    rf.close();
}

void write_matrix_binary(const double* mat, uint32_t M, const string& fileName) {
    ofstream wf(fileName, ios::out | ios::binary);
    if (!wf.is_open()) {
        cerr << "Cannot open output file!" << endl;
        exit(1);
    }
    wf.write(reinterpret_cast<const char*>(mat), sizeof(double) * M * M);
    wf.close();
}

void matrix_mult_block(double* A, double* B, double* C, int block_size) {
    for (int i = 0; i < block_size; i++)
        for (int j = 0; j < block_size; j++)
            for (int k = 0; k < block_size; k++)
                C[i * block_size + j] += A[i * block_size + k] * B[k * block_size + j];
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int q = static_cast<int>(sqrt(size));
    if (q * q != size) {
        if (rank == 0) cerr << "Number of processes must be a perfect square (e.g., 4, 9, 16, 25, 36, ...)." << endl;
        MPI_Finalize();
        return 1;
    }

    int dims[2] = { q, q }, periods[2] = { 1, 1 };
    MPI_Comm grid_comm;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 1, &grid_comm);

    int coords[2];
    MPI_Cart_coords(grid_comm, rank, 2, coords);
    int row = coords[0], col = coords[1];

    if (rank == 0) read_input();
    MPI_Bcast(&M, 1, MPI_UINT32_T, 0, MPI_COMM_WORLD);

    int block_size = M / q;
    vector<double> A_block(block_size * block_size, 0.0);
    vector<double> B_block(block_size * block_size, 0.0);
    vector<double> C_block(block_size * block_size, 0.0);

    vector<double> A, B;
    auto t_start = steady_clock::now();
    auto read_start = t_start;

    if (rank == 0) {
        A.resize(M * M);
        B.resize(M * M);
        read_matrix_binary(A.data(), M, FileA);
        read_matrix_binary(B.data(), M, FileB);
    }

    MPI_Scatter(A.data(), block_size * block_size, MPI_DOUBLE, A_block.data(), block_size * block_size, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Scatter(B.data(), block_size * block_size, MPI_DOUBLE, B_block.data(), block_size * block_size, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    auto read_end = steady_clock::now();
    if (rank == 0) cout << "Reading Time: " << duration<double, milli>(read_end - read_start).count() << " ms" << endl;

    MPI_Comm row_comm, col_comm;
    MPI_Comm_split(grid_comm, row, col, &row_comm);
    MPI_Comm_split(grid_comm, col, row, &col_comm);

    MPI_Status status;
    for (int step = 0; step < q; step++) {
        int src = (row + step) % q;
        int A_root_rank;
		int A_coords[2] = {row, src};
        MPI_Cart_rank(grid_comm, A_coords, &A_root_rank);

        if (src == col)
            matrix_mult_block(A_block.data(), B_block.data(), C_block.data(), block_size);

        MPI_Bcast(A_block.data(), block_size * block_size, MPI_DOUBLE, src, row_comm);

        MPI_Sendrecv_replace(B_block.data(), block_size * block_size, MPI_DOUBLE,
                             (col + 1) % q, 0,
                             (col - 1 + q) % q, 0,
                             col_comm, &status);
    }

    vector<double> C;
    if (rank == 0) C.resize(M * M);

    MPI_Gather(C_block.data(), block_size * block_size, MPI_DOUBLE,
               C.data(), block_size * block_size, MPI_DOUBLE,
               0, MPI_COMM_WORLD);

    auto comp_end = steady_clock::now();
    if (rank == 0) cout << "Computation Time: " << duration<double, milli>(comp_end - read_end).count() << " ms" << endl;

    auto write_start = steady_clock::now();
    if (rank == 0) write_matrix_binary(C.data(), M, FileC);
    auto write_end = steady_clock::now();

    if (rank == 0) {
        cout << "Writing Time: " << duration<double, milli>(write_end - write_start).count() << " ms" << endl;
        cout << "Total Time: " << duration<double, milli>(write_end - t_start).count() << " ms" << endl;
    }

    MPI_Comm_free(&row_comm);
    MPI_Comm_free(&col_comm);
    MPI_Comm_free(&grid_comm);

    MPI_Finalize();
    return 0;
}
