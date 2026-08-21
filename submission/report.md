# Báo cáo MLOps AWS

**Cloud:** AWS S3 + EC2

## 1. Bằng chứng

Ảnh được đặt trong `submission/Screenshot/` theo đúng thứ tự:

1. `01-mlflow-3-runs.png` - MLflow có ít nhất ba thí nghiệm.
2. `02-mlflow-best-run.png` - bộ tham số tốt nhất.
3. `03-s3-dvc-data.png` - dữ liệu DVC dưới prefix `dvc/`.
4. `04-github-secrets-names.png` - danh sách tên GitHub Secrets, không hiển thị giá trị bí mật.
5. `05-github-actions-all-green.png` - lần chạy pipeline đầu tiên, bốn job đều xanh.
6. `06-api-health-predict.png` - kết quả `/health` và `/predict`.
7. `07-continuous-training.png` - pipeline được kích hoạt bởi commit dữ liệu mới.
8. `08-eval-gate-failed.png` - minh họa Eval gate chặn model yếu.
9. `09-github-actions-restored.png` - lần chạy sau khi khôi phục params tốt nhất.

## 2. Thí nghiệm và mô hình

Ba cấu hình đã được so sánh trên MLflow. Cấu hình được chọn là:

```yaml
n_estimators: 300
max_depth: null
min_samples_split: 2
```

Lý do: đây là kết quả cao nhất trong các lần chạy local, với **accuracy = 0.6820** và **f1_score = 0.6811**. Eval gate CI/CD được đặt là **0.68** theo cho phép của giảng viên, vì vậy model đạt điều kiện để deploy.

| Tập dữ liệu         | Số mẫu | Accuracy | F1 score |
| ------------------- | -----: | -------: | -------: |
| Lần đầu             |  2.998 |   0.6820 |   0.6811 |
| Sau bổ sung dữ liệu |  5.996 |   0.7460 |   0.7449 |

Dữ liệu bổ sung đã cải thiện accuracy từ 0.6820 lên 0.7460 (+0.0640) và f1_score từ 0.6811 lên 0.7449 (+0.0639). Hai giá trị của lần 5.996 mẫu được lấy từ `outputs/metrics.json` trong artifact của run GitHub Actions được kích hoạt bởi commit dữ liệu.

## 3. Khó khăn và cách xử lý

- Python 3.13 không tương thích với các pin cũ của scikit-learn, nên cập nhật bộ dependency sang MLflow 2.18.0, scikit-learn 1.6.1 và pandas 2.2.3.
- DVC xung đột với `pathspec` cũ; cập nhật `pathspec` lên 0.12.1 và dùng DVC 3.50.1 với S3.
- PowerShell khác cú pháp Bash (`$env:`, `${vmIp}`); các lệnh Windows được viết lại trong `tasks/aws-windows.md`.
- EC2 service ban đầu không có AWS credentials; gắn IAM Role cho EC2 để boto3 tải `models/latest/model.pkl` từ S3.
- Private key SSH cần quyền file riêng trên Windows; xử lý bằng `icacls`.
- GitHub Actions chỉ deploy sau khi Eval pass; systemd service phải được tạo trước trên EC2.

## 4. Kết luận

Pipeline đã gồm MLflow tracking, DVC/S3 versioning, GitHub Actions với Test -> Train -> Eval -> Deploy và FastAPI trên EC2. Commit dữ liệu mới cập nhật con trỏ DVC, đẩy object lên S3 trước, sau đó kích hoạt lại pipeline để huấn luyện và deploy model mới.
