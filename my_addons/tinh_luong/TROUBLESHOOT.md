# Hướng dẫn khắc phục: Dữ liệu chấm công không được lấy vào bảng lương

## ⚠️ Vấn đề
Khi tạo bảng lương và bấm "Tính lương", dữ liệu chấm công (giờ đi trễ, về sớm, OT, nghỉ phép) không được populate vào chi tiết lương.

---

## 🔍 Nguyên nhân có thể

### 1️⃣ Nhân viên chưa cài đặt **Lương cơ bản**
- ❌ **Lương cơ bản = 0 hoặc trống** → Không thể tính được lương/giờ
- ✅ **Khắc phục**: 
  1. Vào danh sách **Nhân viên**
  2. Mở từng nhân viên → Tab **"Lương"**
  3. Nhập **Lương cơ bản** (bắt buộc)
  4. Nhập các phụ cấp nếu có

### 2️⃣ Nhân viên chưa được **gán ca làm việc**
- ❌ **Ca làm = Trống** → Không biết giờ bắt đầu/kết thúc
- ✅ **Khắc phục**:
  1. Vào danh sách **Nhân viên**
  2. Mở từng nhân viên
  3. Nhập **Ca làm việc** (vd: "Ca 8-17")
  4. Nếu chưa có ca → Tạo mới: **Danh sách Ca làm việc** → **Tạo mới**

### 3️⃣ **Chấm công nằm ngoài khoảng ngày** của bảng lương
- ❌ **Ví dụ**: Bảng lương tháng 5 (1/5 - 31/5) nhưng chấm công vào tháng 4 → Không lấy được
- ✅ **Khắc phục**:
  1. Kiểm tra khoảng ngày **Từ ngày - Đến ngày** của bảng lương
  2. Kiểm tra ngày chấm công của nhân viên (xem tab **"Chấm công chi tiết"**)
  3. Đảm bảo chấm công nằm trong khoảng ngày bảng lương

### 4️⃣ **Dữ liệu chấm công chưa được lưu đúng**
- ❌ **Thiếu giờ vào hoặc giờ ra**
- ✅ **Khắc phục**:
  1. Vào **Nhân viên** → Tab **"Chấm công chi tiết"**
  2. Kiểm tra mỗi ngày công có đủ **Giờ vào** và **Giờ ra** không
  3. Trạng thái phải là **"Bình thường"** hoặc có vi phạm (không phải rỗng)

---

## 🆘 Cách tìm lỗi nhanh chóng

Khi bấm "Tính lương", hệ thống sẽ show **thông tin gỡ lỗi** cho mỗi nhân viên:

1. **Mở bảng lương** → **Chi tiết lương** → **Mở một nhân viên**
2. Kéo xuống xem **phần "🔍 Thông tin gỡ lỗi"**:
   - ✓ **Lương cơ bản**: Hiển thị mức lương
   - ✓ **Ca làm**: Hiển thị ca đã gán
   - ✓ **Số chấm công tìm được**: Số lần được lấy (phải > 0)

### Ví dụ:
```
❌ Lương cơ bản: Chưa nhập
❌ Ca làm (Debug): Chưa gán ca
ℹ️ Số chấm công tìm được: 0
```
→ Cần nhập lương và gán ca

---

## ✅ Quy trình chuẩn để tính lương

### Bước 1: Thiết lập nhân viên
1. Vào **Nhân viên**
2. Mở từng nhân viên
3. **Tab "Lương"** → Nhập:
   - ✓ Lương cơ bản
   - ✓ Ca làm việc (nếu chưa có)
   - ✓ Phụ cấp (nếu có)

### Bước 2: Kiểm tra chấm công
1. **Tab "Chấm công chi tiết"** → Xem các ngày công
2. Đảm bảo mỗi ngày có **Giờ vào** + **Giờ ra**

### Bước 3: Tạo bảng lương
1. Vào **Bảng lương** → **Tạo mới**
2. Nhập **Từ ngày** và **Đến ngày** (vd: 1/5/2026 - 31/5/2026)
3. Bấm **"Tính lương"** → Hệ thống tự:
   - ✓ Thêm tất cả nhân viên vào chi tiết
   - ✓ Lấy dữ liệu chấm công trong khoảng ngày
   - ✓ Tính tổng giờ công, OT, phạt
   - ✓ Tính tiền lương

---

## 🚀 Nếu vẫn không được

### A. Kiểm tra logs
- Mở **Developer Tools** (hoặc terminal)
- Tìm các warning/error của payroll
- Vd: `[TenNhanVien] Tìm được 0 bản chấm công`

### B. Kiểm tra SQL (nếu có kiến thức)
```sql
-- Xem chấm công của nhân viên
SELECT * FROM nhan_su_cham_cong 
WHERE nhan_vien_id = <ID nhân viên>
ORDER BY ngay DESC;

-- Xem settings lương
SELECT luong_co_ban, ca_lam_id 
FROM nhan_su_nhan_vien 
WHERE id = <ID nhân viên>;
```

### C. Liên hệ hỗ trợ
Cung cấp thông tin:
- Tên nhân viên
- Khoảng ngày bảng lương
- Screenshot phần "🔍 Thông tin gỡ lỗi"

---

## 💡 Mẹo
- 🔄 Sau khi nhập xong chấm công, bấm lại **"Tính lương"** (hệ thống sẽ re-calculate)
- 📊 Sử dụng **"Xem lương tháng"** (trong form nhân viên) để test trước khi tính bảng lương toàn bộ
- 📅 Chắc chắn khoảng ngày bảng lương **bao gồm** toàn bộ ngày công

---

**Version**: 1.0  
**Last Updated**: 2026-05-01
