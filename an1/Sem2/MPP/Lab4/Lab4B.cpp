#include <mpi.h>
#include <iostream>
#include <fstream>
#include <cmath>
#include <vector>
#include <chrono>

using namespace std;
using namespace std::chrono;

int main(int argc, char* argv[]) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Determine the process grid dimensions
    int q = static_cast<int>(sqrt(size));
    if (q * q != size) {
        if (rank == 0) {
            cerr << "Number of processes must be a perfect square." << endl;
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    // Create a 2D Cartesian communicator
    int dims[2] = { q, q };
    int periods[2] = { 1, 1 }; // Enable wrap-around connections
    MPI_Comm cart_comm;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 1, &cart_comm);

    int coords[2];
    MPI_Cart_coords(cart_comm, rank, 2, coords);
    int row = coords[0];
    int col = coords[1];

    // Read matrix size and file names from input.txt
    uint32_t M;
    string fileA, fileB, fileC;
    if (rank == 0) {
        ifstream input("input.txt");
        if (!input) {
            cerr << "Cannot open input.txt" << endl;
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }
        input >> M >> fileA >> fileB >> fileC;
    }
    // Broadcast M and file names to all processes
    MPI_Bcast(&M, 1, MPI_UINT32_T, 0, MPI_COMM_WORLD);
    int filename_length = 256;
    char a_filename[256], b_filename[256], c_filename[256];
    if (rank == 0) {
        strncpy(a_filename, fileA.c_str(), filename_length);
        strncpy(b_filename, fileB.c_str(), filename_length);
        strncpy(c_filename, fileC.c_str(), filename_length);
    }
    MPI_Bcast(a_filename, filename_length, MPI_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(b_filename, filename_length, MPI_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(c_filename, filename_length, MPI_CHAR, 0, MPI_COMM_WORLD);

    // Calculate block size
    int block_size = M / q;
    if (M % q != 0) {
        if (rank == 0) {
            cerr << "Matrix size M must be divisible by sqrt(number of processes)." << endl;
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    // Allocate memory for local blocks
    vector<double> A_block(block_size * block_size);
    vector<double> B_block(block_size * block_size);
    vector<double> C_block(block_size * block_size, 0.0);

    // Start timing for reading
    auto read_start = steady_clock::now();

    // Parallel reading of A and B blocks
    MPI_File file;
    MPI_Offset offset;
    MPI_Datatype block_type;
    MPI_Type_vector(block_size, block_size, M, MPI_DOUBLE, &block_type);
    MPI_Type_create_resized(block_type, 0, sizeof(double), &block_type);
    MPI_Type_commit(&block_type);

    int gsizes[2] = { M, M };
    int distribs[2] = { MPI_DISTRIBUTE_BLOCK, MPI_DISTRIBUTE_BLOCK };
    int dargs[2] = { MPI_DISTRIBUTE_DFLT_DARG, MPI_DISTRIBUTE_DFLT_DARG };
    int psizes[2] = { q, q };

    MPI_Datatype filetype;
    MPI_Type_create_darray(size, rank, 2, gsizes, distribs, dargs, psizes,
                           MPI_ORDER_C, MPI_DOUBLE, &filetype);
    MPI_Type_commit(&filetype);

    // Read A_block
    MPI_File_open(cart_comm, a_filename, MPI_MODE_RDONLY, MPI_INFO_NULL, &file);
    MPI_File_set_view(file, 0, MPI_DOUBLE, filetype, "native", MPI_INFO_NULL);
    MPI_File_read_all(file, A_block.data(), block_size * block_size, MPI_DOUBLE, MPI_STATUS_IGNORE);
    MPI_File_close(&file);

    // Read B_block
    MPI_File_open(cart_comm, b_filename, MPI_MODE_RDONLY, MPI_INFO_NULL, &file);
    MPI_File_set_view(file, 0, MPI_DOUBLE, filetype, "native", MPI_INFO_NULL);
    MPI_File_read_all(file, B_block.data(), block_size * block_size, MPI_DOUBLE, MPI_STATUS_IGNORE);
    MPI_File_close(&file);

    auto read_end = steady_clock::now();
    double read_time = duration<double, milli>(read_end - read_start).count();

    // Start timing for computation
    auto comp_start = steady_clock::now();

    // Initial alignment for Cannon's algorithm
    int left, right, up, down;
    MPI_Cart_shift(cart_comm, 1, -row, &right, &left);
    MPI_Sendrecv_replace(A_block.data(), block_size * block_size, MPI_DOUBLE,
                         left, 0, right, 0, cart_comm, MPI_STATUS_IGNORE);

    MPI_Cart_shift(cart_comm, 0, -col, &down, &up);
    MPI_Sendrecv_replace(B_block.data(), block_size * block_size, MPI_DOUBLE,
                         up, 0, down, 0, cart_comm, MPI_STATUS_IGNORE);

    // Perform Cannon's algorithm
    for (int step = 0; step < q; ++step) {
        // Local matrix multiplication
        for (int i = 0; i < block_size; ++i) {
            for (int j = 0; j < block_size; ++j) {
                double sum = 0.0;
                for (int k = 0; k < block_size; ++k) {
                    sum += A_block[i * block_size + k] * B_block[k * block_size + j];
                }
                C_block[i * block_size + j] += sum;
            }
        }

        // Shift A left by one
        MPI_Cart_shift(cart_comm, 1, -1, &right, &left);
        MPI_Sendrecv_replace(A_block.data(), block_size * block_size, MPI_DOUBLE,
                             left, 0, right, 0, cart_comm, MPI_STATUS_IGNORE);

        // Shift B up by one
        MPI_Cart_shift(cart_comm, 0, -1, &down, &up);
        MPI_Sendrecv_replace(B_block.data(), block_size * block_size, MPI_DOUBLE,
                             up, 0, down, 0, cart_comm, MPI_STATUS_IGNORE);
    }

    auto comp_end = steady_clock::now();
    double comp_time = duration<double, milli>(comp_end - comp_start).count();

    // Start timing for writing
    auto write_start = steady_clock::now();

    // Gather C_blocks to rank 0
    vector<double> C;
    if (rank == 0) {
        C.resize(M * M);
    }

    MPI_Gather(C_block.data(), block_size * block_size, MPI_DOUBLE,
               C.data(), block_size * block_size, MPI_DOUBLE,
               0, cart_comm);

    // Rank 0 writes the result to the output file
    if (rank == 0) {
        ofstream output(c_filename, ios::out | ios::binary);
        if (!output) {
            cerr << "Cannot open output file." << endl;
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }
        output.write(reinterpret_cast<char*>(C.data()), M * M * sizeof(double));
        output.close();
    }

    auto write_end = steady_clock::now();
    double write_time = duration<double, milli>(write_end - write_start).count();

    // Output timing information
    double total_time = duration<double, milli>(write_end - read_start).count();
    if (rank == 0) {
        cout << "Read time: " << read_time << " ms" << endl;
        cout << "Computation time: " << comp_time << " ms" << endl;
        cout << "Write time: " << write_time << " ms" << endl;
        cout << "Total execution time: " << total_time << " ms" << endl;
    }

    // Clean up
    MPI_Type_free(&block_type);
    MPI_Type_free(&filetype);
    MPI_Comm_free(&cart_comm);
    MPI_Finalize();
    return 0;
}
