<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KVI Product Price Battle Dashboard</title>
    <!-- โหลด Tailwind CSS ผ่าน CDN สำหรับการจัดหน้า -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- โหลด Lucide Icons สำหรับรูปไอคอนต่างๆ -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Sarabun', sans-serif; }
    </style>
</head>
<body class="min-h-screen bg-slate-50 p-4 md:p-8 text-slate-800">

    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header Section -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center bg-white p-6 rounded-xl shadow-sm border border-slate-200 gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    📊 KVI Product Price Battle
                </h1>
                <p class="text-slate-500 mt-1 text-sm flex items-center gap-1" id="statusText">
                    <i data-lucide="check-circle-2" class="w-4 h-4 text-green-500"></i>
                    ระบบแสดงผลข้อมูลราคาคงที่
                </p>
            </div>
            
            <div class="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <i data-lucide="search" class="h-4 w-4 text-slate-400"></i>
                    </div>
                    <input
                        type="text"
                        id="searchInput"
                        placeholder="ค้นหาสินค้า..."
                        class="pl-10 pr-4 py-2 w-full sm:w-64 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                    />
                </div>
                
                <button 
                    id="refreshBtn"
                    class="flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-white transition-all bg-slate-800 hover:bg-slate-900 shadow-sm"
                >
                    <i data-lucide="refresh-cw" id="refreshIcon" class="h-4 w-4"></i>
                    <span id="refreshText">อัปเดตข้อมูล</span>
                </button>
            </div>
        </div>

        <!-- Table Section -->
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden overflow-x-auto">
            <div class="bg-[#fcebe6] py-2 px-4 text-center border-b border-slate-200 font-bold text-slate-800">
                Update <span id="lastUpdateText">19/03/2026 10:00:00</span>
            </div>
            <table class="w-full text-sm text-left whitespace-nowrap">
                <thead class="text-xs text-slate-800 bg-[#fcebe6] border-b border-slate-200">
                    <tr>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">category_name</th>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">KVI Product</th>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">CJ</th>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">Lotus</th>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">Big C</th>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">7-Eleven</th>
                        <th class="px-4 py-4 font-bold text-center border-r border-slate-300">Diff Market</th>
                        <th class="px-4 py-4 font-bold text-center">Price Battle</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- ข้อมูลจะถูกสร้างด้วย JavaScript -->
                </tbody>
            </table>
        </div>

    </div>

    <!-- Script สำหรับควบคุมการทำงาน -->
    <script>
        // ข้อมูลตั้งต้น
        let appData = [
            { id: 1, category: "FISH SAUCE", name: "ทิพรสน้ำปลาขวดเพท700cc", cj: 29, lotus: 29.5, bigc: 29.5, seven: 29.5 },
            { id: 2, category: "FISH SAUCE", name: "เมกาเชฟน้ำปลา500cc", cj: 39, lotus: 42, bigc: 39, seven: 39 },
            { id: 3, category: "FISH SAUCE", name: "ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเหลือง700ml", cj: 21, lotus: 21, bigc: 21, seven: 24 },
            { id: 4, category: "FISH SAUCE", name: "ปลาหมึกน้ำปลาแท้ขวดเพทฉลากเขียว700ml", cj: 29, lotus: 27, bigc: 27, seven: 29 },
            { id: 5, category: "SAUCE", name: "แม่ครัวฉลากทองซอสหอย300cc", cj: 37, lotus: 37, bigc: 36, seven: 37 },
            { id: 6, category: "SAUCE", name: "แม่ครัวฉลากทองซอสหอย600cc", cj: 49, lotus: 52, bigc: 50, seven: 52 },
            { id: 7, category: "SAUCE", name: "ภูเขาทองซอสปรุงรสฝาเขียวเพท1L", cj: 53, lotus: 56, bigc: 53, seven: 56 },
            { id: 8, category: "SAUCE", name: "แม็กกี้ซอสปรุงรส680cc", cj: 34.5, lotus: 36, bigc: 34.5, seven: 42 },
            { id: 9, category: "SAUCE", name: "แม็กกี้ซอสปรุงอาหารสูตรเข้มเข้าเนื้อ680", cj: 34.5, lotus: 36, bigc: 38, seven: 42 },
            { id: 10, category: "SAUCE", name: "เด็กสมบูรณ์ซอสหอยนางรมสูตรเข้มข้น800g", cj: 47, lotus: 29, bigc: 29, seven: 39 },
            { id: 11, category: "SAUCE", name: "เด็กสมบูรณ์ซีอิ๊วขาวสูตร1 700cc", cj: 55, lotus: 47, bigc: 44, seven: 45 },
            { id: 12, category: "SAUCE", name: "เด็กสมบูรณ์ซีอิ๊วขาวสูตร1 1000cc", cj: 62, lotus: 65, bigc: 65, seven: 66 },
        ];

        let searchTerm = "";

        // เริ่มต้นการทำงานของ Lucide Icons
        lucide.createIcons();

        // ฟังก์ชันคำนวณส่วนต่างและสถานะ
        function calculateStats(item) {
            const minCompetitorPrice = Math.min(item.lotus, item.bigc, item.seven);
            const diff = item.cj - minCompetitorPrice;
            
            let status = ""; let bgColor = ""; let textColor = "";
            
            if (diff < 0) {
                status = "Win"; bgColor = "bg-green-100"; textColor = "text-green-800";
            } else if (diff === 0) {
                status = "Match"; bgColor = "bg-yellow-100"; textColor = "text-yellow-800";
            } else {
                status = "Lose"; bgColor = "bg-red-500"; textColor = "text-white";
            }
            return { diff, status, bgColor, textColor };
        }

        // ฟังก์ชันสร้างหน้าตาราง
        function renderTable() {
            const tbody = document.getElementById("tableBody");
            tbody.innerHTML = "";

            // กรองข้อมูลตามคำค้นหา
            const filteredData = appData.filter(item => 
                item.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                item.category.toLowerCase().includes(searchTerm.toLowerCase())
            );

            filteredData.forEach((item, index) => {
                const stats = calculateStats(item);
                const showCategory = index === 0 || filteredData[index - 1].category !== item.category;

                // การจัดรูปแบบ Diff (ถ้ามากกว่า 0 ให้พื้นหลังแดง)
                const diffClass = stats.diff > 0 ? 'bg-red-500 text-white font-bold' : '';

                const tr = document.createElement("tr");
                tr.className = "bg-white border-b border-slate-200 hover:bg-slate-50 transition-colors";
                tr.innerHTML = `
                    <td class="px-4 py-2 font-medium text-slate-700 border-r border-slate-200 text-center align-middle whitespace-normal w-28">
                        ${showCategory ? item.category : ""}
                    </td>
                    <td class="px-4 py-2 font-medium text-slate-800 border-r border-slate-200 whitespace-normal min-w-[200px]">${item.name}</td>
                    <td class="px-4 py-2 text-center border-r border-slate-200 font-bold text-orange-600 bg-orange-50/30">${item.cj}</td>
                    <td class="px-4 py-2 text-center border-r border-slate-200">${item.lotus}</td>
                    <td class="px-4 py-2 text-center border-r border-slate-200">${item.bigc}</td>
                    <td class="px-4 py-2 text-center border-r border-slate-200">${item.seven}</td>
                    <td class="px-4 py-2 text-center border-r border-slate-200 ${diffClass}">${stats.diff.toFixed(1)}</td>
                    <td class="px-4 py-2 text-center font-bold ${stats.bgColor} ${stats.textColor}">${stats.status}</td>
                `;
                tbody.appendChild(tr);
            });

            // อัปเดตไอคอนให้แสดงผลอีกครั้ง
            lucide.createIcons();
        }

        // ระบบค้นหา
        document.getElementById("searchInput").addEventListener("input", function(e) {
            searchTerm = e.target.value;
            renderTable();
        });

        // ระบบปุ่มรีเฟรช (จำลอง)
        document.getElementById("refreshBtn").addEventListener("click", function() {
            const btn = this;
            const icon = document.getElementById("refreshIcon");
            const text = document.getElementById("refreshText");
            const status = document.getElementById("statusText");

            // เปลี่ยนสถานะเป็นกำลังโหลด
            btn.classList.add("bg-slate-400", "cursor-not-allowed");
            btn.classList.remove("bg-slate-800", "hover:bg-slate-900");
            icon.classList.add("animate-spin");
            text.innerText = "กำลังอัปเดต...";
            status.innerHTML = `<i data-lucide="server" class="w-4 h-4 text-blue-500 animate-pulse"></i> กำลังเชื่อมต่อข้อมูล...`;
            lucide.createIcons();

            // หน่วงเวลา 1 วินาที
            setTimeout(() => {
                // คืนค่าสถานะ
                btn.classList.remove("bg-slate-400", "cursor-not-allowed");
                btn.classList.add("bg-slate-800", "hover:bg-slate-900");
                icon.classList.remove("animate-spin");
                text.innerText = "อัปเดตข้อมูล";
                
                // อัปเดตเวลาล่าสุด
                const now = new Date();
                document.getElementById("lastUpdateText").innerText = now.toLocaleString('th-TH');
                status.innerHTML = `<i data-lucide="check-circle-2" class="w-4 h-4 text-green-500"></i> อัปเดตข้อมูลล่าสุดสำเร็จ`;
                lucide.createIcons();

            }, 1000);
        });

        // แสดงผลตารางครั้งแรกตอนเปิดหน้าเว็บ
        renderTable();

    </script>
</body>
</html>
