use std::thread;

fn main() {
    let mut data = vec![1, 2, 3];

    // Compile error: cannot move out while still borrowed
    let handle = thread::spawn(|| {
        data.push(4); // not allowed
    });

    handle.join().unwrap();
}
