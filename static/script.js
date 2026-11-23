const video = document.getElementById('camera');
const gazeDirectionSpan = document.getElementById('gazeDirection');
const numFacesSpan = document.getElementById('numFaces');

// Mengambil stream dari webcam
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error('Error accessing webcam:', err);
    });

function submitExam() {
    const answers = [
        { question: "1. Menurut anda fitur deteksi apa yang perlu ditambahkan?", answer: document.getElementById('answer1').value },
        { question: "2. Berikan saya masukan lainnya", answer: document.getElementById('answer2').value }
    ];

    fetch('/submit_exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answers: answers }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Exam submitted successfully!');
        }
    })
    .catch(error => {
        console.error('Error submitting exam:', error);
    });
}

// Fungsi untuk mengirim frame ke server
function processFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');

        fetch('/process_frame', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error processing frame:', data.error);
            } else {
                gazeDirectionSpan.textContent = data.gaze_direction;
                numFacesSpan.textContent = data.num_faces;
            }
        })
        .catch(error => {
            console.error('Error sending frame:', error);
        });
    });

    setTimeout(processFrame, 1000); // Panggil kembali setiap detik
}

// Mulai pemrosesan frame setelah video dimuat
video.addEventListener('loadeddata', processFrame);
