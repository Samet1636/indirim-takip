"""
Bir dosyayı GitHub deposuna, git kullanmadan, GitHub API üzerinden yükler.

A101 GitHub sunucularından taranamadığı için kendi bilgisayarımızda tarıyor ve sonucu
(data/imports/a101.json) bu yolla depoya gönderiyoruz. Bilgisayardaki proje klasörüne
dokunulmadığı için GitHub Desktop'ta çakışma yaşanmaz.

Gerekli ortam değişkeni:  GH_TOKEN  (sadece bu depoya "Contents: Read and write" yetkili token)
İsteğe bağlı:             GH_REPO   (varsayılan: Samet1636/indirim-takip)
"""
from __future__ import annotations

import base64
import os

import requests

DEFAULT_REPO = "Samet1636/indirim-takip"


def upload_file(path_in_repo: str, content: bytes, message: str,
                repo: str | None = None, token: str | None = None, branch: str = "main") -> str:
    token = token or os.environ.get("GH_TOKEN")
    repo = repo or os.environ.get("GH_REPO") or DEFAULT_REPO
    if not token:
        raise RuntimeError("GH_TOKEN ortam değişkeni tanımlı değil (setx GH_TOKEN \"...\")")
    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    # Dosya zaten varsa güncellemek için mevcut sürümün kimliği (sha) gerekiyor
    r = requests.get(url, headers=headers, params={"ref": branch}, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": message, "content": base64.b64encode(content).decode(), "branch": branch}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=headers, json=body, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub yükleme hatası {r.status_code}: {r.text[:300]}")
    return r.json()["commit"]["html_url"]
