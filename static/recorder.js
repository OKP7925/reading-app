let mediaRecorder;
let recordedChunks = [];

// 録音開始
document.getElementById("recordButton").onclick = () => {
    countdownAndStartRecording();
};

function countdownAndStartRecording() {
    const countdownTexts = ["3", "2", "1", "GO!"];
    let index = 0;

    const countdownDiv = document.createElement("div");
    countdownDiv.id = "countdown";
    countdownDiv.style.position = "fixed";
    countdownDiv.style.top = "50%";
    countdownDiv.style.left = "50%";
    countdownDiv.style.transform = "translate(-50%, -50%)";
    countdownDiv.style.fontSize = "5em";
    countdownDiv.style.fontWeight = "bold";
    countdownDiv.style.backgroundColor = "rgba(0, 0, 0, 0.7)";
    countdownDiv.style.color = "white";
    countdownDiv.style.padding = "20px";
    countdownDiv.style.borderRadius = "20px";
    countdownDiv.style.textAlign = "center";
    document.body.appendChild(countdownDiv);

    const countdownInterval = setInterval(() => {
        countdownDiv.innerText = countdownTexts[index];
        index++;
        if (index >= countdownTexts.length) {
            clearInterval(countdownInterval);
            document.body.removeChild(countdownDiv);
            startRecording();
        }
    }, 1000);
}

function startRecording() {
    recordedChunks = [];
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Safari向け優先設定（wav）
            let options = { mimeType: 'audio/wav' };
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                // 他ブラウザ用 fallback（webm）
                options = { mimeType: 'audio/webm' };
            }

            console.log("使用するMimeType:", options.mimeType);  // 追加ログ

            mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) recordedChunks.push(e.data);
            };
            mediaRecorder.onstop = () => {
                const blob = new Blob(recordedChunks, { type: options.mimeType });
                console.log("録音BlobのMIMEタイプ:", blob.type);  // 追加ログ
                const url = URL.createObjectURL(blob);
                document.getElementById("audioPlayer").src = url;
                document.getElementById("audioPlayer").style.display = "block";
                recordedBlob = blob;
                document.getElementById("playButton").disabled = false;
                document.getElementById("retryButton").disabled = false;
                document.getElementById("submitButton").disabled = false;
            };
            mediaRecorder.start();
            document.getElementById("stopButton").disabled = false;
        });
}

document.getElementById("stopButton").onclick = () => {
    mediaRecorder.stop();
    document.getElementById("stopButton").disabled = true;
};

document.getElementById("playButton").onclick = () => {
    document.getElementById("audioPlayer").play();
};

document.getElementById("retryButton").onclick = () => {
    document.getElementById("audioPlayer").style.display = "none";
    document.getElementById("playButton").disabled = true;
    document.getElementById("retryButton").disabled = true;
    document.getElementById("submitButton").disabled = true;
    countdownAndStartRecording();
};

// ファイル名生成
function generateFilename() {
    const urlParts = window.location.pathname.split('/');
    if (urlParts.length < 6) {
        console.error("URLが不正です。");
        return "unknown_recording.webm";
    }

    const publisher = urlParts[2];
    const grade = urlParts[3];
    const unit = urlParts[4];
    const scene = urlParts[5];
    const studentId = document.getElementById("studentId").value || "unknown";

    return `${publisher}_${grade}_${unit}_${scene}_${studentId}_recording.webm`;
}

// 提出処理
document.getElementById("submitButton").onclick = () => {
    const filename = generateFilename();
    const formData = new FormData();
    formData.append("audio_data", recordedBlob, filename);

    fetch("/upload", { method: "POST", body: formData })
        .then(response => response.text())
        .then(result => {
            document.body.innerHTML = result;
        })
        .catch(error => {
            console.error("提出エラー:", error);
        });
};