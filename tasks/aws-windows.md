# Chay lab AWS tren Windows 11 PowerShell

Tai lieu nay thay cho cac lenh `bash`, `export`, `sed` va `chmod` trong huong dan goc.
Mo VS Code trong thu muc project va mo terminal **PowerShell**.

Ban co the dung truc tiep environment conda `DL-torch`; `.venv` khong bat buoc. Cac lenh ben duoi dung interpreter dang active (`python`).

## 0. Cai cong cu

Cai Python, Git, AWS CLI va tao tai khoan GitHub/AWS. May ban dang co Python 3.13.5, nen dung lenh `python` thay cho Python Launcher `py`. Kiem tra:

```powershell
python --version
python -m pip --version
git --version
aws --version
```

Neu `python` khong chay, cai Python tu python.org va chon **Add python.exe to PATH**. Trong VS Code, chon `Python: Select Interpreter` va chon `.venv` sau khi tao moi truong. Khong can cai hoac su dung `py.exe`.

Cau hinh AWS CLI bang IAM user co quyen quan tri trong giai doan tao tai nguyen:

```powershell
aws configure
aws sts get-caller-identity
```

Nhap Access Key ID, Secret Access Key, region (vi du `us-east-1`) va output `json`. Khi AWS CLI hien prompt Secret Access Key, dan truc tiep vao prompt roi nhan Enter; khong dat secret trong lenh PowerShell. Ky tu `$` va `/` trong secret se bi PowerShell phan tich neu dat khong dung cach. Khong luu secret vao file project, chat, screenshot hoac git.

Neu secret da tung duoc dan vao terminal/chat, vao AWS IAM ngay lap tuc de **Deactivate/Delete access key cu**, tao access key moi, sau do chay lai `aws configure`. Neu dung user CI, co the kiem tra key bang `aws iam list-access-keys --user-name mlops-lab-ci` va xoa key cu trong AWS Console.

## 1. Tao moi truong va du lieu

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python generate_data.py
```

Neu muon dung `.venv` thay cho conda, co the thoat environment hien tai truoc khi tao moi truong:

```powershell
conda deactivate
python -m venv .venv
```

Sau khi kich hoat thanh cong, dau nhac lenh se hien `(.venv)`. Kiem tra lai:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

Ket qua `sys.executable` phai tro den `D:\Vin\K3-Track2-Day21-2A202601029-DoNgocBich\.venv\Scripts\python.exe` (khong phai `anaconda3\envs\DL-torch\python.exe`). Neu van thay ca `(.venv) (DL-torch)`, dong terminal nay, mo terminal moi, chay `conda deactivate` cho den khi mat `(DL-torch)`, sau do kich hoat lai `.venv`.

Bo dependency da duoc cap nhat de co wheel cho Python 3.13. Neu pip van bao khong co wheel phu hop, cai Python 3.12 bang `winget`, dong mo lai VS Code, kiem tra lai `python --version`, sau do tao lai `.venv`:

```powershell
winget install --id Python.Python.3.12 -e
Remove-Item -Recurse -Force .venv
python -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Neu PowerShell chan script activation, mo PowerShell voi quyen user va chay mot lan:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Kiem tra ba file CSV da tao:

```powershell
Get-ChildItem data
```

## 2. Chay MLflow local

Ban dang o dung vi tri sau khi `python generate_data.py` in ra 2998/500/2998 mau. Khong can chay lai script tao du lieu.

Dat bien moi truong cho cua so PowerShell hien tai:

```powershell
$env:MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
$env:MLFLOW_ARTIFACT_ROOT = (Join-Path (Get-Location) "mlartifacts")
```

`params.yaml` mac dinh:

```yaml
n_estimators: 100
max_depth: 5
min_samples_split: 2
```

Chay ba thi nghiem, sua `params.yaml` giua cac lan:

```powershell
python src/train.py
# Sua params.yaml: n_estimators: 50, max_depth: 3
python src/train.py
# Sua params.yaml: n_estimators: 200, max_depth: 10, min_samples_split: 5
python src/train.py
```

Mo cua so PowerShell thu hai, vao project va kich hoat `.venv`:

```powershell
.\.venv\Scripts\Activate.ps1
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Mo `http://localhost:5000`, chon run co accuracy cao nhat va ghi lai params do vao `params.yaml`. Dong UI bang `Ctrl+C` khi xong.

**CHUP MAN HINH 1 - MLflow:** Chup man hinh danh sach it nhat 3 runs, trong do thay cac gia tri params khac nhau va cac metric `accuracy`, `f1_score`. Chup them man hinh run tot nhat neu danh sach khong hien day du thong tin.

## 3. Tao S3 bucket va policy

Dat bien cho cua so hien tai. Bucket phai unique toan cau, chi dung chu thuong, so va dau gach ngang:

```powershell
$env:AWS_REGION = "us-east-1"
$env:BUCKET = "mlops-lab-dongocbich-20260821"
aws s3 mb "s3://$env:BUCKET" --region $env:AWS_REGION
```

Tao file policy bang here-string cua PowerShell:

```powershell
@"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::$($env:BUCKET)",
        "arn:aws:s3:::$($env:BUCKET)/*"
      ]
    }
  ]
}
"@ | Set-Content -Encoding utf8 s3-policy.json

aws iam create-policy `
  --policy-name mlops-lab-s3-policy `
  --policy-document file://s3-policy.json
```

Ghi lai ARN policy trong output. Tao user CI rieng va gan policy. Thay `ACCOUNT_ID` bang 12 chu so tai khoan AWS:

```powershell
$accountId = (aws sts get-caller-identity --query Account --output text)
$policyArn = "arn:aws:iam::$accountId:policy/mlops-lab-s3-policy"
aws iam create-user --user-name mlops-lab-ci
aws iam attach-user-policy --user-name mlops-lab-ci --policy-arn $policyArn
aws iam create-access-key --user-name mlops-lab-ci
```

Luu AccessKeyId va SecretAccessKey vao password manager. Chi dung chung cho GitHub Secrets, khong commit.

## 4. Cau hinh DVC voi S3

Trong project, sau khi `.venv` dang active:

```powershell
dvc init
dvc remote add -d myremote "s3://$env:BUCKET/dvc"
dvc remote modify myremote region $env:AWS_REGION
```

DVC se dung credential da cau hinh bang `aws configure`. Neu khong dung profile default, dat bien moi truong trong terminal:

```powershell
$env:AWS_ACCESS_KEY_ID = "<ACCESS_KEY_ID>"
$env:AWS_SECRET_ACCESS_KEY = "<SECRET_ACCESS_KEY>"
$env:AWS_DEFAULT_REGION = $env:AWS_REGION
```

Track va day du lieu len S3:

```powershell
dvc add data/train_phase1.csv
dvc add data/eval.csv
dvc add data/train_phase2.csv
git add data/*.dvc .gitignore .dvc/config
git commit -m "feat: track datasets with DVC"
dvc push
aws s3 ls "s3://$env:BUCKET/dvc/" --recursive
```

**CHUP MAN HINH 2 - S3/DVC:** Chup S3 Console tai bucket cua ban, hien prefix `dvc/` va cac object DVC. Co the chup them terminal hien `dvc push` thanh cong.

Chi commit file `.dvc`, khong commit CSV. Neu `dvc init` tao thay doi `.dvc/config`, phai commit file nay de GitHub runner biet remote.

## 5. Tao EC2 va IAM Role

Tao key pair va luu private key tai project chi de SSH local:

```powershell
aws ec2 create-key-pair --key-name mlops-deploy --query KeyMaterial --output text | Set-Content -Encoding ascii mlops-deploy.pem
```

Lay AMI Ubuntu 22.04 moi nhat trong region:

```powershell
$ami = aws ec2 describe-images `
  --owners 099720109477 `
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" `
  --query "sort_by(Images,&CreationDate)[-1].ImageId" --output text
$ami
```

Tao security group trong default VPC va mo port SSH/API. Trong thuc te nen thay `0.0.0.0/0` cua port 22 bang IP cua ban `/32`:

```powershell
$vpc = aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text
$sg = aws ec2 create-security-group --group-name mlops-sg --description "MLOps lab SG" --vpc-id $vpc --query GroupId --output text
aws ec2 authorize-security-group-ingress --group-id $sg --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $sg --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

Tao instance. Neu lenh bao khong tim thay subnet, chon subnet default trong region va them `--subnet-id`:

```powershell
$instanceId = aws ec2 run-instances `
  --image-id $ami --instance-type t2.micro --key-name mlops-deploy `
  --security-group-ids $sg `
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mlops-serve}]' `
  --query "Instances[0].InstanceId" --output text
$instanceId
```

Gan IAM Role cho EC2 de VM doc model S3, khong copy AWS secret len VM. Dung policy S3 phia tren cho role:

```powershell
@'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
'@ | Set-Content -Encoding ascii trust-policy.json
aws iam create-role --role-name mlops-serve-role --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name mlops-serve-role --policy-arn $policyArn
aws iam create-instance-profile --instance-profile-name mlops-serve-profile
aws iam add-role-to-instance-profile --instance-profile-name mlops-serve-profile --role-name mlops-serve-role
aws ec2 associate-iam-instance-profile --instance-id $instanceId --iam-instance-profile Name=mlops-serve-profile
```

Lay IP va cho instance qua trang thai running:

```powershell
$vmIp = aws ec2 describe-instances --instance-ids $instanceId --query "Reservations[0].Instances[0].PublicIpAddress" --output text
$vmIp
```

## 6. Cai API tren EC2

Tren Windows, SSH dung OpenSSH co san trong Windows 11:

```powershell
ssh -i .\mlops-deploy.pem ubuntu@$vmIp
```

Trong VM:

```bash
sudo apt update && sudo apt install -y python3-pip
python3 -m pip install fastapi uvicorn scikit-learn joblib boto3
mkdir -p ~/models ~/src
exit
```

Copy API len VM:

```powershell
scp -i .\mlops-deploy.pem .\src\serve.py ubuntu@${vmIp}:~/src/serve.py
ssh -i .\mlops-deploy.pem ubuntu@$vmIp
```

Trong VM, tao systemd service. Thay bucket trong dong `Environment` bang gia tri that:

```bash
sudo tee /etc/systemd/system/mlops-serve.service > /dev/null <<'EOF'
[Unit]
Description=MLOps Model Inference Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="S3_BUCKET=TEN_BUCKET_THAT"
Environment="AWS_DEFAULT_REGION=us-east-1"
ExecStart=/usr/bin/python3 /home/ubuntu/src/serve.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable mlops-serve
exit
```

Chua start service cho den sau pipeline train thanh cong vi model chua co tren S3.

## 7. GitHub Secrets va push pipeline

Trong GitHub: **Settings > Secrets and variables > Actions > New repository secret**. Tao cac secret:

| Secret | Gia tri |
|---|---|
| `AWS_ACCESS_KEY_ID` | AccessKeyId cua `mlops-lab-ci` |
| `AWS_SECRET_ACCESS_KEY` | SecretAccessKey tuong ung |
| `AWS_REGION` | `us-east-1` |
| `CLOUD_BUCKET` | Ten bucket S3 |
| `VM_HOST` | IP public cua EC2 |
| `VM_USER` | `ubuntu` |
| `VM_SSH_KEY` | Toan bo noi dung `mlops-deploy.pem` |

Commit workflow va code. GitHub Actions se chay test trong runner, du khong can ban chay test local:

```powershell
git add .
git commit -m "feat: add AWS CI/CD pipeline and serving API"
git branch -M main
git remote -v
git push -u origin main
```

Theo doi tab **Actions**. Khi Train va Eval xanh, chay lan dau tren VM:

```powershell
ssh -i .\mlops-deploy.pem ubuntu@$vmIp "sudo systemctl start mlops-serve"
Invoke-RestMethod "http://${vmIp}:8000/health"
$body = '{"features":[7.4,0.70,0.00,1.9,0.076,11.0,34.0,0.9978,3.51,0.56,9.4,0]}'
Invoke-RestMethod "http://${vmIp}:8000/predict" -Method Post -ContentType "application/json" -Body $body
```

**CHUP MAN HINH 3 - API:** Chup ket qua `health` tra ve `status: ok` va ket qua `predict` co `prediction`/`label`. Neu dung curl trong Git Bash, chup man hinh terminal curl cung duoc.

**CHUP MAN HINH 4 - GitHub Actions thanh cong:** Trong tab Actions, mo run do commit pipeline kich hoat va chup man hinh hien ca 4 job `Unit Test`, `Train`, `Eval`, `Deploy` deu xanh. Chup them log `Health check passed` trong job Deploy neu co the.

## 8. Huấn luyen lai voi du lieu moi

Thuc hien dung thu tu de runner luon thay du lieu moi truoc khi pipeline chay:

```powershell
python add_new_data.py
dvc add data/train_phase1.csv
git add data/train_phase1.csv.dvc
git commit -m "data: bo sung 2998 mau du lieu moi (train_phase2)"
dvc push
git push origin main
```

`dvc push` phai thanh cong truoc `git push`. Commit `.dvc` thay doi se kich hoat workflow. Kiem tra lai endpoint sau khi job Deploy xanh.

## 9. Kiem tra eval gate (nguong 0.65)

Voi accuracy hien tai khoang `0.676`, model se vuot qua gate `0.65` va duoc deploy. Neu muon minh hoa gate that bai, tam sua `params.yaml` thanh `n_estimators: 1`, `max_depth: 1`, push va xem job Eval fail, Deploy bi bo qua. Sau do phuc hoi bo tham so tot nhat, commit va push lai. Khong xoa run MLflow hoac artifact de con anh chup minh chung.

**CHUP MAN HINH 5 - Eval gate that bai:** Chup run GitHub Actions voi job `Eval` mau do, log hien accuracy nho hon `0.70`, va job `Deploy` bi bo qua. Sau khi chup xong, phuc hoi params tot nhat va push lai de co run xanh.

## 10. Don dep tai nguyen AWS

Lab co the phat sinh chi phi EC2/EBS. Sau khi nop bai, dung instance va xoa tai nguyen neu khong con can:

```powershell
aws ec2 terminate-instances --instance-ids $instanceId
aws s3 rm "s3://$env:BUCKET" --recursive
aws s3 rb "s3://$env:BUCKET"
```

Khong xoa bucket truoc khi ban da chup anh hoac tai artifact can nop.
