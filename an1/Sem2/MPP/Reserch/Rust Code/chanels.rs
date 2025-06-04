use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        tx.send("Hello from the thread!").unwrap();
    });

    let received = rx.recv().unwrap();
    println!("Main received: {}", received);
}
