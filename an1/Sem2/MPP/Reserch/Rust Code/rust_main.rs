use std::thread;

fn main() {
    // let handle = thread::spawn(|| {
    //     println!("Thread is running!");
    // });

    // handle.join().unwrap();

    ten_threds();
}

fn ten_threds() {
    let mut handles = vec![];

    for i in 1..=10 {
        let handle = thread::spawn(move || {
            println!("Thread {} is running!", i);
        });

        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }
}
