# stop-all-windows.ps1
# Dung TAT CA tien trinh/container PWP dang chay truoc khi khoi dong lai - bat buoc chay script
# nay truoc moi lan `uvicorn`/`npm run dev`/`docker compose up` moi, de tranh dung loi da gap o
# Sprint 1.1b: 1 tien trinh cu van giu cong 8001/3000 va am tham tra loi bang code CU, khien
# tuong nham la code MOI khong hoat dong du thuc ra code moi hoan toan dung.
#
# Cach dung: mo PowerShell tai thu muc goc PWP (vd: C:\PWP), chay:
#   .\scripts\windows\stop-all-windows.ps1
#
# An toan khi chay nhieu lan / khi chua co gi dang chay - moi buoc deu boc try/catch,
# khong bao loi do neu khong tim thay tien trinh/container nao.

Write-Host "== Dung Docker Compose (parser-service, gateway, redis) ==" -ForegroundColor Cyan
try {
    docker compose -f docker\docker-compose.yml down 2>$null
    Write-Host "  OK (hoac khong co container nao dang chay)" -ForegroundColor Green
} catch {
    Write-Host "  Bo qua (Docker co the chua cai hoac khong co container nao)" -ForegroundColor Yellow
}

Write-Host "== Kiem tra cong 8001 (Parser Service) va 3000 (Gateway) ==" -ForegroundColor Cyan
foreach ($port in @(8001, 3000, 8002)) {
    $connections = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    if ($connections) {
        Write-Host "  Cong $port dang bi chiem boi:" -ForegroundColor Yellow
        foreach ($line in $connections) {
            $tokens = ($line -split '\s+') | Where-Object { $_ -ne '' }
            $procId = $tokens[-1]
            try {
                $proc = Get-Process -Id $procId -ErrorAction Stop
                Write-Host "    PID $procId -> $($proc.ProcessName)" -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "    Da dung PID $procId" -ForegroundColor Green
            } catch {
                Write-Host "    Khong lay duoc thong tin tien trinh PID $procId (co the da tu thoat)" -ForegroundColor DarkYellow
            }
        }
    } else {
        Write-Host "  Cong $port dang ranh" -ForegroundColor Green
    }
}

Write-Host "== Dung moi tien trinh python/uvicorn/node con sot (thuoc phien dev cu) ==" -ForegroundColor Cyan
foreach ($name in @("python", "uvicorn", "node")) {
    Get-Process -Name $name -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  Dung $($_.ProcessName) (PID $($_.Id))" -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "== Xac nhan lai cong da ranh ==" -ForegroundColor Cyan
foreach ($port in @(8001, 3000, 8002)) {
    $still = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    if ($still) {
        Write-Host "  CANH BAO: cong $port VAN dang bi chiem - kiem tra thu cong bang:" -ForegroundColor Red
        Write-Host "    netstat -ano | findstr :$port" -ForegroundColor Red
    } else {
        Write-Host "  Cong ${port}: OK, da ranh" -ForegroundColor Green
    }
}

Write-Host "`nXong. Gio co the khoi dong lai service (uvicorn/npm run dev/docker compose up)." -ForegroundColor Cyan