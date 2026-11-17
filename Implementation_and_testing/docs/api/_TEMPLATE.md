# <Tên module> – API contract  (BE: … / FE: …)  – viết ngày 1, sửa phải báo cả cặp

## <Tên màn hình>
- **URL:** `GET /registration/sections/?semester=1&q=...&page=1`
- **Quyền:** STUDENT
- **Template:** `templates/registration/open_sections.html`
- **Context:** `sections[{section_code, course_name, credits, teacher, schedule, classroom, remaining, max_capacity, state}]`, `page_info`
- **Hành động:** `POST /registration/sections/<id>/register/` → redirect + message thành công / lỗi
- **Mã lỗi:** SECTION_FULL, ALREADY_REGISTERED, SCHEDULE_CONFLICT, PREREQ_NOT_MET, REGISTRATION_CLOSED
