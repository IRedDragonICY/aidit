$(document).ready(function() {
    $('#toggle-sidebar').on('click', function() {
        $('#sidebar-section').toggleClass('collapsed');
    });

    let chatSocket = null;
    let isProcessing = false;

    function initializeWebSocket() {
        chatSocket = new WebSocket('ws://localhost:1010/ws/chat');

        chatSocket.onopen = function() {
            // Koneksi berhasil, menunggu pesan
        };

        chatSocket.onmessage = function(event) {
            if (event.data.startsWith('{')) {
                const data = JSON.parse(event.data);
                if (data.status === 'completed') {
                    isProcessing = false;
                    $('#action-button i').removeClass('fa-stop').addClass('fa-paper-plane');
                    if ($('#chat-box .message.ai').length === 1) {
                        showFileUploadForm();
                    }
                } else if (data.status === 'file_processed') {
                    isProcessing = false;
                    $('#action-button i').removeClass('fa-stop').addClass('fa-paper-plane');
                    $('#loading').hide();
                    $('#progress-area').hide();
                    // Tampilkan tabel analisis
                    displayAnalysisResults(data.results);
                    // Hapus form unggah file
                    $('#upload-form').closest('.message.ai').remove();
                } else if (data.error) {
                    isProcessing = false;
                    $('#action-button i').removeClass('fa-stop').addClass('fa-paper-plane');
                    $('#loading').hide();
                    $('#progress-area').hide();
                    appendMessage('ai', "Maaf, terjadi kesalahan: " + data.error, 'warning');
                    scrollChatToBottom();
                } else if (data.status === 'reset_completed') {
                    $('#chat-box').empty();
                    appendMessage('ai', "Percakapan telah direset.");
                }
            } else {
                if (isProcessing && $('#progress-area').is(':visible')) {
                    $('#progress-text').append(event.data);
                } else {
                    appendToLastMessage('ai', event.data);
                }
                scrollChatToBottom();
            }
        };

        chatSocket.onerror = function(error) {
            appendMessage('ai', "Maaf, terjadi kesalahan pada koneksi.", 'warning');
            scrollChatToBottom();
        };

        chatSocket.onclose = function() {
            console.log("Chat WebSocket closed");
        };
    }

    initializeWebSocket();

    function showFileUploadForm() {
        const fileUploadForm = `
            <div class="message ai">
                <div class="message-content">
                    <form id="upload-form">
                        <div class="mb-3">
                            <label for="pdfFile" class="form-label"><i class="fa fa-file-pdf text-danger"></i> Silakan unggah file PDF Anda:</label>
                            <input type="file" class="form-control" id="pdfFile" name="pdfFile" accept="application/pdf" required>
                        </div>
                        <button type="submit" class="btn btn-primary"><i class="fa fa-upload"></i> Unggah dan Proses</button>
                    </form>
                    <div id="loading" class="text-center mt-4" style="display: none;">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Memproses...</span>
                        </div>
                        <p class="mt-2">File Anda sedang diproses, harap tunggu...</p>
                    </div>
                    <div id="upload-error" class="alert alert-danger mt-3 d-none" role="alert">
                        Terjadi kesalahan saat memproses file.
                    </div>
                </div>
            </div>
        `;
        $('#chat-box').append(fileUploadForm);
        scrollChatToBottom();

        $('#upload-form').on('submit', function(e) {
            e.preventDefault();

            if (isProcessing) {
                alert("Proses sedang berjalan, harap tunggu.");
                return;
            }

            const fileInput = $('#pdfFile')[0];
            if (fileInput.files.length === 0) {
                alert("Silakan pilih file PDF.");
                return;
            }

            const file = fileInput.files[0];
            const reader = new FileReader();
            reader.onload = function(event) {
                const arrayBuffer = event.target.result;
                const uint8Array = new Uint8Array(arrayBuffer);

                $('#loading').show();
                $('#upload-error').addClass('d-none');
                isProcessing = true;

                chatSocket.send(JSON.stringify({
                    command: 'upload_file',
                    pdf_bytes: Array.from(uint8Array)
                }));

                $('#progress-area').show();
                $('#progress-text').text('Memulai ekstraksi data...');

                $('#action-button i').removeClass('fa-paper-plane').addClass('fa-stop');
            };
            reader.readAsArrayBuffer(file);
        });
    }

    $('#action-button').on('click', function(e) {
        e.preventDefault();
        if (isProcessing) {
            chatSocket.send(JSON.stringify({ command: 'stop' }));
            isProcessing = false;
            $('#progress-area').hide();
            $('#action-button i').removeClass('fa-stop').addClass('fa-paper-plane');
        } else {
            const userInput = $('#user-input').val().trim();
            if (userInput === "") {
                alert("Silakan tulis pesan Anda.");
                return;
            }

            appendMessage('user', userInput);
            $('#user-input').val('');
            scrollChatToBottom();

            isProcessing = true;

            chatSocket.send(JSON.stringify({
                command: 'user_message',
                message: userInput
            }));

            $('#action-button i').removeClass('fa-paper-plane').addClass('fa-stop');
        }
    });

    $('#new-chat-btn').on('click', function() {
        chatSocket.send(JSON.stringify({ command: 'reset' }));
    });

    $(document).on('click', '.delete-button', function() {
        const messageElement = $(this).closest('.message');
        const index = messageElement.index();
        chatSocket.send(JSON.stringify({ command: 'delete_message', message_index: index }));
        messageElement.remove();
    });

    const appendMessage = (sender, message, type = 'message') => {
        const messageClass = sender === 'user' ? 'user' : 'ai';
        const messageTypeClass = type === 'warning' ? 'warning' : '';
        const messageElement = `
            <div class="message ${messageClass} ${messageTypeClass}">
                <div class="message-content">
                    ${escapeHtml(message)}
                </div>
                ${type !== 'warning' ? `
                <div class="message-actions">
                    <button class="btn btn-sm btn-secondary delete-button"><i class="fa fa-trash"></i></button>
                    ${sender === 'ai' ? '<button class="btn btn-sm btn-secondary regenerate-button"><i class="fa fa-sync"></i></button>' : ''}
                </div>` : ''}
            </div>
        `;
        $('#chat-box').append(messageElement);
    };

    const appendToLastMessage = (sender, message) => {
        const messageClass = sender === 'user' ? 'user' : 'ai';
        const lastMessage = $('#chat-box .message').last();
        if (lastMessage.length && lastMessage.hasClass(messageClass) && !lastMessage.hasClass('warning')) {
            const contentDiv = lastMessage.find('.message-content');
            contentDiv.html(contentDiv.html() + escapeHtml(message));
        } else {
            appendMessage(sender, message);
        }
    };

    const scrollChatToBottom = () => {
        const chatBox = $('#chat-box');
        chatBox.scrollTop(chatBox[0].scrollHeight);
    };

    const escapeHtml = (text) => {
        return $('<div>').text(text).html();
    };

    $(document).on('click', '.regenerate-button', function() {
        if (isProcessing) {
            alert("Proses sedang berjalan, harap tunggu.");
            return;
        }
        isProcessing = true;
        chatSocket.send(JSON.stringify({ command: 'regenerate' }));
        $('#action-button i').removeClass('fa-paper-plane').addClass('fa-stop');
    });

    const displayAnalysisResults = (results) => {
        let tableHtml = `
            <table id="analysis-results-table" class="table table-striped table-hover">
                <thead>
                    <tr>
        `;

        const columns = Object.keys(results[0]);
        columns.forEach(column => {
            tableHtml += `<th>${escapeHtml(column)}</th>`;
        });

        tableHtml += `
                    </tr>
                </thead>
                <tbody>
        `;

        results.forEach(row => {
            tableHtml += '<tr>';
            columns.forEach(column => {
                let cellData = row[column];
                if (typeof cellData === 'number') {
                    if (column === 'Year') {
                        cellData = parseInt(cellData);
                    } else {
                        cellData = cellData.toFixed(4);
                    }
                }
                tableHtml += `<td>${escapeHtml(cellData)}</td>`;
            });
            tableHtml += '</tr>';
        });

        tableHtml += `
                </tbody>
            </table>
        `;

        const messageElement = `
            <div class="message ai">
                <div class="message-content">
                    <p>Berikut adalah hasil analisis Beneish M-Score:</p>
                    ${tableHtml}
                </div>
            </div>
        `;
        $('#chat-box').append(messageElement);

        $('#analysis-results-table').DataTable({
            responsive: true,
            paging: false,
            searching: false,
            info: false
        });

        scrollChatToBottom();
    };
});
