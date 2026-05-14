# AI Camera Stream Processor (YOLOv8 & ByteTrack)

## Giới thiệu
Dự án này là một hệ thống xử lý luồng video từ camera (RTSP hoặc file video) sử dụng mô hình YOLOv8 để phát hiện đối tượng và ByteTrack để theo dõi. Hệ thống có khả năng đếm số lượng đối tượng đi vào/ra một khu vực định nghĩa trước (polygon) và băng qua một đường thẳng, đồng thời hiển thị các thông số này theo thời gian thực.

## Tính năng chính
-   **Phát hiện và Theo dõi đối tượng**: Sử dụng YOLOv8 (Ultralytics) để phát hiện và ByteTrack để theo dõi các đối tượng (mặc định là người).
-   **Hỗ trợ GPU (CUDA)**: Tự động phát hiện và sử dụng GPU NVIDIA để tăng tốc xử lý nếu có.
-   **Xử lý luồng thời gian thực**: Đọc và xử lý luồng video từ các nguồn RTSP hoặc file video.
-   **Đếm đối tượng trong vùng (Polygon)**: Xác định và đếm số lượng đối tượng hiện có trong một khu vực đa giác được định nghĩa.
-   **Đếm đối tượng qua đường thẳng (Line)**: Đếm số lượng đối tượng đi vào và đi ra khi băng qua một đường thẳng.
-   **Cấu hình linh hoạt**: Dễ dàng cấu hình các tham số như độ tin cậy của mô hình, đường dẫn mô hình, tọa độ vùng/đường kẻ, độ phân giải xử lý, v.v.
-   **Công cụ lấy tọa độ trực quan**: Cung cấp một công cụ riêng biệt (`toadopolygon.py`) để dễ dàng xác định tọa độ vùng đa giác và đường kẻ trên khung hình video.
-   **Hiển thị FPS**: Hiển thị tốc độ xử lý khung hình (FPS) theo thời gian thực.
-   **Tối ưu hiệu suất**: Sử dụng đa luồng (threading) và quản lý hàng đợi (Queue) để tối ưu hóa luồng dữ liệu và tránh tràn bộ nhớ.

## Yêu cầu hệ thống
-   **Python 3.8+**
-   **NVIDIA GPU** (khuyến nghị cho hiệu suất tốt nhất)
-   **NVIDIA Drivers** (đã cài đặt và cập nhật)
-   **CUDA Toolkit** (tương thích với phiên bản PyTorch)

## Cài đặt

### 1. Clone Repository
```bash
git clone <đường_dẫn_đến_repo_của_bạn>
cd intern(2)
```

### 2. Tạo và kích hoạt môi trường ảo
```bash
python -m venv .venv
# Trên Windows
.venv\Scripts\activate
# Trên macOS/Linux
source .venv/bin/activate
```

### 3. Cài đặt các thư viện Python
```bash
pip install -r requirements.txt
```
*(Nếu file `requirements.txt` chưa có, bạn có thể tạo nó bằng cách chạy `pip freeze > requirements.txt` sau khi cài đặt tất cả các thư viện cần thiết, hoặc cài đặt thủ công: `pip install opencv-python numpy PyYAML ultralytics torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`)*

**Lưu ý về PyTorch (GPU)**:
Để đảm bảo PyTorch sử dụng GPU, hãy cài đặt phiên bản hỗ trợ CUDA. Ví dụ cho CUDA 11.8:
```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
Kiểm tra xem GPU có được nhận diện không:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```
Kết quả phải là `True`.

### 4. Tải trọng số YOLOv8
Tải file trọng số `yolov8n.pt` (hoặc phiên bản khác) và đặt vào thư mục `resources/weights/`.
Bạn có thể tải từ trang chủ Ultralytics: [YOLOv8 Models](https://docs.ultralytics.com/models/yolov8/#models)

### 5. Cài đặt FFmpeg
FFmpeg được sử dụng để giả lập luồng RTSP từ file video.
-   **Windows**: Tải từ [ffmpeg.org](https://ffmpeg.org/download.html), giải nén và thêm thư mục `bin` vào biến môi trường `PATH`.
-   **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install ffmpeg`
-   **macOS (Homebrew)**: `brew install ffmpeg`

### 6. Cài đặt MediaMTX (RTSP Server)
MediaMTX là một RTSP server nhẹ, được khuyến nghị để nhận luồng từ FFmpeg và phân phối cho ứng dụng của bạn.
-   Tải phiên bản phù hợp với hệ điều hành của bạn từ [MediaMTX Releases](https://github.com/bluenviron/mediamtx/releases).
-   Giải nén và chạy file `mediamtx.exe` (trên Windows) hoặc `mediamtx` (trên Linux/macOS). Nó sẽ chạy trên `rtsp://localhost:8554`.

## Cấu hình dự án

### 1. `resources/config/setting.py`
File này chứa tất cả các cấu hình quan trọng của hệ thống:
-   `RTSP_URL`: Đường dẫn luồng RTSP đầu vào.
-   `MODEL_PATH`: Đường dẫn đến file trọng số YOLOv8.
-   `CONFIDENCE`: Ngưỡng tin cậy cho phát hiện đối tượng.
-   `TARGET_WIDTH`, `TARGET_HEIGHT`: Độ phân giải chuẩn mà hệ thống sẽ xử lý. **Quan trọng: Các tọa độ vùng/đường kẻ phải được lấy trên độ phân giải này.**
-   `ZONE_POLYGON`: Danh sách các điểm tạo thành vùng đa giác.
-   `COUNTING_LINE`: Danh sách 4 điểm tạo thành đường thẳng đếm.
-   `BBOX_SHRINK_FACTOR`: Tỷ lệ thu nhỏ bounding box khi hiển thị.
-   `BBOX_THICKNESS`: Độ dày nét vẽ của bounding box và các đường kẻ.
-   `TRACKER_TYPE`: Loại tracker được sử dụng (mặc định là `bytetrack.yaml`).

### 2. Sử dụng `toadopolygon.py` để lấy tọa độ
Để xác định tọa độ `ZONE_POLYGON` và `COUNTING_LINE` một cách trực quan:
```bash
python toadopolygon.py
```
-   **Nhấn 'L'**: Chuyển sang chế độ vẽ **Đường thẳng**. Click 2 điểm để tạo đường.
-   **Nhấn 'P'**: Chuyển sang chế độ vẽ **Đa giác**. Click nhiều điểm để tạo vùng.
-   **Chuột trái**: Thêm điểm.
-   **Chuột phải**: Xóa điểm cuối cùng.
-   **Nhấn 'S'**: In tọa độ ra console. Copy và dán vào `setting.py`.
-   **Nhấn 'C'**: Xóa tất cả các điểm trong chế độ hiện tại.
-   **Nhấn 'ESC'**: Thoát công cụ.

## Cách sử dụng

### 1. Khởi động MediaMTX
Chạy file `mediamtx.exe` (hoặc `mediamtx`) đã tải về. Đảm bảo nó đang chạy ở `rtsp://localhost:8554`.

### 2. Giả lập luồng RTSP (nếu dùng file video)
Mở một terminal mới và sử dụng FFmpeg để đẩy file video lên MediaMTX. Thay thế `path/to/your/video.mp4` bằng đường dẫn thực tế của bạn.
```bash
ffmpeg -re -stream_loop -1 -i "path/to/your/video.mp4" -c copy -f rtsp -rtsp_transport tcp rtsp://localhost:8554/live
```
**Lưu ý**: Giữ cửa sổ terminal này mở trong suốt quá trình bạn muốn ứng dụng nhận luồng.

### 3. Chạy ứng dụng chính
Mở một terminal khác, kích hoạt môi trường ảo và chạy `main.py`:
```bash
.venv\Scripts\activate # hoặc source .venv/bin/activate
python main.py
```
Ứng dụng sẽ bắt đầu xử lý luồng video, hiển thị kết quả phát hiện, theo dõi, đếm và FPS.

## Khắc phục sự cố

-   **`torch.cuda.is_available()` trả về `False`**:
    -   Đảm bảo bạn đã cài đặt đúng phiên bản PyTorch hỗ trợ CUDA.
    -   Kiểm tra driver NVIDIA và CUDA Toolkit đã được cài đặt đúng cách.
    -   Đảm bảo bạn đang chạy trong môi trường ảo đã cài đặt PyTorch CUDA.
-   **Luồng video bị giật lag hoặc lỗi `OutOfMemoryError`**:
    -   Đảm bảo bạn đang sử dụng `MediaMTX` và lệnh FFmpeg với `-c copy`.
    -   Kiểm tra xem `TARGET_WIDTH` và `TARGET_HEIGHT` trong `setting.py` có quá cao không. Giảm độ phân giải có thể cải thiện hiệu suất.
    -   Kiểm tra tài nguyên hệ thống (CPU, GPU, RAM) có bị quá tải không.
-   **Lỗi tọa độ (`Bad argument` trong OpenCV)**:
    -   Đảm bảo `BBOX_THICKNESS` trong `setting.py` là một số nguyên.
    -   Đảm bảo bạn đã sử dụng `toadopolygon.py` để lấy tọa độ trên cùng độ phân giải `TARGET_WIDTH`x`TARGET_HEIGHT` và dán chính xác vào `setting.py`.

---
