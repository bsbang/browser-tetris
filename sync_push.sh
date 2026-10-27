#!/bin/bash
git add .
COMMIT_MSG="loop-sync: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG"
git push -u origin main
echo "[+] GitHub 원격 저장소 동기화 완료!"

if command -v rclone &> /dev/null && rclone listremotes | grep -q "gdrive:"; then
    rclone sync "$HOME/SecondBrain" gdrive:SecondBrain --exclude ".git/**"
    echo "[+] Google Drive (SecondBrain) 문서 금고 미러링 완료!"
fi
