# API测试脚本
$ErrorActionPreference = "Continue"

Write-Host "==================================" -ForegroundColor Green
Write-Host "  API功能验证测试 (Port 8003)" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

$BASE_URL = "http://127.0.0.1:8003"

# 测试1: 健康检查
Write-Host "Test 1: Health Check" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -TimeoutSec 5
    Write-Host "  PASS: Status = $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Server may not be running. Please start it manually:" -ForegroundColor Yellow
    Write-Host "  cd D:\AIposition\backend\job-platform" -ForegroundColor Yellow
    Write-Host "  .\start_server.bat" -ForegroundColor Yellow
    exit 1
}

# 测试2: 获取验证码
Write-Host ""
Write-Host "Test 2: Send Verification Code" -ForegroundColor Cyan
try {
    $codeResp = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/send-verification-code?phone=13800138000" -Method Post -TimeoutSec 5
    $code = $codeResp.code
    Write-Host "  PASS: Code = $code" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 测试3: 注册用户
Write-Host ""
Write-Host "Test 3: Register User" -ForegroundColor Cyan
try {
    $regBody = @{
        phone = "13800138000"
        password = "Test1234"
        display_name = "TestUser"
        role = "seeker"
        verification_code = $code
    } | ConvertTo-Json

    $regResp = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/register" `
        -Method Post `
        -ContentType "application/json" `
        -Body $regBody `
        -TimeoutSec 5

    $token = $regResp.access_token
    $userId = $regResp.user.id
    Write-Host "  PASS: UserID = $userId, Phone = $($regResp.user.phone)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}

# 测试4: 获取当前用户信息
Write-Host ""
Write-Host "Test 4: Get Current User Info" -ForegroundColor Cyan
if ($token) {
    try {
        $me = Invoke-RestMethod -Uri "$BASE_URL/api/v1/users/me" `
            -Headers @{Authorization = "Bearer $token"} `
            -TimeoutSec 5
        Write-Host "  PASS: Phone = $($me.phone), Name = $($me.display_name)" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 测试5: 验证码限流
Write-Host ""
Write-Host "Test 5: Rate Limiting (should fail on 2nd request)" -ForegroundColor Cyan
try {
    $r1 = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/send-verification-code?phone=13900139000" `
        -Method Post -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  Request 1: PASS (allowed)" -ForegroundColor Green

    Start-Sleep -Seconds 1

    try {
        $r2 = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/send-verification-code?phone=13900139000" `
            -Method Post -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  Request 2: FAIL (should be rate limited but was not)" -ForegroundColor Red
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 429) {
            Write-Host "  Request 2: PASS (correctly rate limited with 429)" -ForegroundColor Green
        } else {
            Write-Host "  Request 2: Unexpected status $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  Request 1 FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "  Test Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
