/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted, useRef, onWillUnmount } from "@odoo/owl";

class MobileScan extends Component {
    setup() {
        this.videoRef = useRef("video");
        this.phieuId = this.props.action?.params?.phieu_id;
        this.stream = null;
        this.codeReader = null;
        this.active = true;

        onMounted(() => {
            setTimeout(() => { if (this.active) this.startCamera(); }, 500);
        });

        onWillUnmount(() => {
            this.active = false;
            this.stopCamera();
        });
    }

    onClose = () => {
        console.log("--- Bắt đầu đóng Camera ---");
        this.active = false; 

        this.stopCamera();

        this.env.services.action.doAction({ type: "ir.actions.act_window_close" });

        setTimeout(() => {
            const currentPath = window.location.hash;
            if (currentPath.includes('quan_ly_nhap_scan_barcode')) {
                console.log("--- Odoo Action treo, dùng History Back ---");
                window.history.back();
            }
        }, 400);

        setTimeout(() => {
            this.env.services.action.doAction({ type: 'ir.actions.client', tag: 'soft_reload' });
        }, 800);
    }

    stopCamera() {
        try {
            if (this.stream) {
                this.stream.getTracks().forEach(track => {
                    track.stop();
                    track.enabled = false;
                });
                this.stream = null;
            }
            if (this.codeReader) {
                this.codeReader.reset();
                this.codeReader = null;
            }
        } catch (e) {
            console.error("Lỗi khi dừng camera:", e);
        }
    }

    async startCamera() {
        const video = this.videoRef.el;
        if (!video) return;
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "environment" } 
            });
            video.srcObject = this.stream;
            this.initScanner(video);
        } catch (err) {
            console.error(err);
        }
    }

async initScanner(videoElement) {
        try {
            const ZXingModule = await import("https://unpkg.com/@zxing/browser@latest?module");
            this.codeReader = new ZXingModule.BrowserMultiFormatReader();
            
            this.codeReader.decodeFromVideoDevice(undefined, videoElement, async (result) => {
                if (result && this.active && !this.isProcessing) {
                    this.isProcessing = true;

                    try {
                        await this.env.services.orm.call(
                            'quan_ly_nhap.phieu_nhap',
                            'process_scanned_barcode',
                            [result.text, this.phieuId]
                        );
                        alert("✅ Đã quét xong mã: " + result.text + "\nNhấn OK để quét mã tiếp theo.");

                    } catch (e) {
                        alert("❌ Lỗi: " + e.message);
                    } finally {
                        this.isProcessing = false;
                    }
                }
            });
        } catch (e) {
            console.error("Lỗi khởi tạo máy quét:", e);
        }
    }
}

MobileScan.template = "quan_ly_nhap.MobileScan";
registry.category("actions").add("quan_ly_nhap_scan_barcode", MobileScan);