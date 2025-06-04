use rayon::prelude::*;

fn main() {
    let nums = vec![1, 2, 3, 4, 5];

    let squared_sum: i32 = nums.par_iter()
        .map(|x| x * x)
        .sum();

    println!("Sum of squares: {}", squared_sum);
}
