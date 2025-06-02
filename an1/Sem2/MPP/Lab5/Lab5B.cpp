#include <mpi.h>
#include <omp.h>
#include <iostream>
#include <fstream>
#include <cmath>
#include <vector>
#include <chrono>

using namespace std;

int M, num_threads;
string FileA, FileB, FileC;

void read_input(string inputFile) {
    ifstream in(inputFile);
    if (!in.is_open()) {
        cerr << "Failed to open input.txt\n";
        exit(1);
    }
    in >> M >> FileA >> FileB >> FileC;
    in.close();
}

void read_matrix_block(double* mat_block, const string& filename, int M, int block_size, int row_block, int col_block) {
    ifstream in(filename, ios::binary);
    if (!in.is_open()) {
        cerr << "Cannot open file " << filename << endl;
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    for (int i = 0; i < block_size; ++i) {
        int row_index = row_block * block_size + i;
        in.seekg((row_index * M + col_block * block_size) * sizeof(double), ios::beg);
        in.read(reinterpret_cast<char*>(&mat_block[i * block_size]), sizeof(double) * block_size);
    }

    in.close();
}

void write_matrix_bin(double* mat, const string& filename, int M) {
    ofstream out(filename, ios::binary);
    if (!out.is_open()) {
        cerr << "Cannot open file " << filename << endl;
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    out.write(reinterpret_cast<char*>(mat), sizeof(double) * M * M);
    out.close();
}

void multiply_block(double* A, double* B, double* C, int block_size) {
    #pragma omp parallel for num_threads(num_threads)
    for (int i = 0; i < block_size; i++) {
        for (int j = 0; j < block_size; j++) {
            for (int k = 0; k < block_size; k++) {
                C[i * block_size + j] += A[i * block_size + k] * B[k * block_size + j];
            }
        }
    }
}

void shift_left(double* block, int block_size, int steps, MPI_Comm row_comm) {
    MPI_Status status;
    int block_len = block_size * block_size;
    vector<double> temp(block_len);
    int rank, size;
    MPI_Comm_rank(row_comm, &rank);
    MPI_Comm_size(row_comm, &size);

    int left = (rank - steps + size) % size;
    int right = (rank + steps) % size;

    MPI_Sendrecv(block, block_len, MPI_DOUBLE, left, 0,
                 temp.data(), block_len, MPI_DOUBLE, right, 0, row_comm, &status);
    copy(temp.begin(), temp.end(), block);
}

void shift_up(double* block, int block_size, int steps, MPI_Comm col_comm) {
    MPI_Status status;
    int block_len = block_size * block_size;
    vector<double> temp(block_len);
    int rank, size;
    MPI_Comm_rank(col_comm, &rank);
    MPI_Comm_size(col_comm, &size);

    int up = (rank - steps + size) % size;
    int down = (rank + steps) % size;

    MPI_Sendrecv(block, block_len, MPI_DOUBLE, up, 0,
                 temp.data(), block_len, MPI_DOUBLE, down, 0, col_comm, &status);
    copy(temp.begin(), temp.end(), block);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: mpirun -np <P> ./program <num_threads>\n";
        return 1;
    }

    num_threads = atoi(argv[1]);

    MPI_Init(&argc, &argv);
    int world_rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    auto t_start = chrono::steady_clock::now();

    read_input("input.txt");

    int q = sqrt(world_size);
    if (q * q != world_size || M % q != 0) {
        if (world_rank == 0)
            cerr << "World size must be a square number and M divisible by q!\n";
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int block_size = M / q;
    int coords[2];
    int dims[2] = {q, q}, periods[2] = {1, 1};
    MPI_Comm cart_comm, row_comm, col_comm;

    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 1, &cart_comm);
    MPI_Cart_coords(cart_comm, world_rank, 2, coords);

    int row_block = coords[0];
    int col_block = coords[1];

    MPI_Comm_split(cart_comm, row_block, col_block, &row_comm);
    MPI_Comm_split(cart_comm, col_block, row_block, &col_comm);

    double* A_block = new double[block_size * block_size]();
    double* B_block = new double[block_size * block_size]();
    double* C_block = new double[block_size * block_size]();

    auto r_start = chrono::steady_clock::now();
    read_matrix_block(A_block, FileA, M, block_size, row_block, col_block);
    read_matrix_block(B_block, FileB, M, block_size, row_block, col_block);
    auto r_end = chrono::steady_clock::now();
    double t_read = chrono::duration<double, milli>(r_end - r_start).count();

    auto m_start = chrono::steady_clock::now();
    shift_left(A_block, block_size, row_block, row_comm);
    shift_up(B_block, block_size, col_block, col_comm);

    for (int step = 0; step < q; ++step) {
        multiply_block(A_block, B_block, C_block, block_size);
        shift_left(A_block, block_size, 1, row_comm);
        shift_up(B_block, block_size, 1, col_comm);
    }
    auto m_end = chrono::steady_clock::now();
    double t_mult = chrono::duration<double, milli>(m_end - m_start).count();

    double* C_full = nullptr;
    if (world_rank == 0)
        C_full = new double[M * M]();

    auto w_start = chrono::steady_clock::now();
    MPI_Gather(C_block, block_size * block_size, MPI_DOUBLE, C_full,
               block_size * block_size, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    auto w_end = chrono::steady_clock::now();
    double t_write = chrono::duration<double, milli>(w_end - w_start).count();

    auto t_end = chrono::steady_clock::now();
    double t_total = chrono::duration<double, milli>(t_end - t_start).count();

    if (world_rank == 0) {
        write_matrix_bin(C_full, FileC, M);
        cout << "Matrix size: " << M << " Threads per process: " << num_threads << endl;
        cout << "Read time: " << t_read << " ms\n";
        cout << "Multiplication time: " << t_mult << " ms\n";
        cout << "Write time: " << t_write << " ms\n";
        cout << "Total time: " << t_total << " ms\n";
    }

    delete[] A_block;
    delete[] B_block;
    delete[] C_block;
    if (world_rank == 0)
        delete[] C_full;

    MPI_Finalize();
    return 0;
}
