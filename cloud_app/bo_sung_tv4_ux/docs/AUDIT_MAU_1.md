# Audit mẫu 1: ảnh concept, chưa phải sản phẩm đang chạy

Đối tượng đánh giá là ảnh sáng xanh đã tạo bằng Imagegen và được người dùng chọn. Audit theo Submitting a form, Showing input error và Loading (Checklist Design). Chỉ nhận định những gì ảnh trả lời được; không chấm điểm hoặc tỷ lệ phần trăm. Các đề xuất là quyết định thiết kế, không phải kết quả thử người dùng.

## [Submitting a form — Flows](https://www.checklist.design/flows/submitting-a-form)

| Trạng thái | Mục và mô tả gốc | Nhận xét |
|---|---|---|
| 🟢 Present | **Show button to submit** — Below the form fields, a button to submit the information needs to be present. You can change the copy to fit the form e.g. the button can say “Subscribe” if someone is providing their email address to receive emails. | Có nút “Kiểm tra tin nhắn” dưới các trường nhập, hành động chính rõ. |
| ❔ Can’t tell | **Show loading state after submission** — The user must see the form is in the process of being submitted. Note: also make sure your hover state is considered before they press the button! | Ảnh không hiển thị lúc gửi; cần chạy nguyên mẫu để kiểm tra loading và hover. |
| 🟢 Present | **Show success message when it submits** — The form was submitted! Let’s communicate that back to the user with a clear success message. | Panel kết quả có nhãn Spam, điểm và phản hồi, cho thấy trạng thái đã phân loại. Không chứng minh API thành công. |
| ❔ Can’t tell | **If it doesn't, show an error message** — Sometimes, things don’t work out. If the form can’t submit, because of invalid information or another error, that also needs to be shown. | Ảnh là trạng thái có kết quả; không có ví dụ lỗi. Cần state lỗi hoặc prototype để kiểm tra. |
| ❔ Can’t tell | **An error may occur because of the wrong information** — If the criteria for a text field isn’t met, the form can fail to submit due to that error, and must be detailed. | Chưa thấy trạng thái lỗi đầu vào hoặc tiêu chí validation trong ảnh; không thể xác nhận từ một ảnh tĩnh. |

Các mục chưa thể kết luận cần prototype hoặc trạng thái tương ứng. Ảnh có kết quả không tự cho biết hành vi loading/lỗi.

## [Showing input error — Flows](https://www.checklist.design/flows/showing-input-error)

| Trạng thái | Mục và mô tả gốc | Nhận xét |
|---|---|---|
| ❔ Can’t tell | **Keep the input in default state** — The text field should be checked for errors only after the information has been entered. | Ảnh có nội dung mẫu và kết quả; không phải lần mở đầu nên chưa biết validation có xuất hiện sớm hay không. |
| ❔ Can’t tell | **Allow user to enter information** — Let the user type without interruptions and submit the information aka don't assess as changes are made. | Không thể biết quá trình gõ có bị ngắt bằng ảnh tĩnh. Cần bấm/gõ thử. |
| ❔ Can’t tell | **Signal error after loss of focus** — After the input has lost focus (user has clicked another element), the field should be assessed. Looks like we have an error here! In this case, explain why the error happened, and what is required to resolve it. For accessibility, combine the text with a visual icon that indicates an error was found. | Không có trạng thái blur/lỗi trong ảnh. Nguyên mẫu chọn validate khi submit cho form ngắn, không báo lỗi ngay lúc nhập. |
| ❔ Can’t tell | **Return to default state upon reattempt** — Once the user focuses on the field again, the error message should disappear. If there is an error again, the process will simply repeat until they are able to continue. | Không có trạng thái sửa sau lỗi trong ảnh. Cần kiểm tra khi focus/gõ lại và submit lại. |

Các mục chưa thể kết luận cần prototype hoặc trạng thái tương ứng. Ảnh có kết quả không tự cho biết hành vi loading/lỗi.

## [Loading — Design system](https://www.checklist.design/design-system/loading)

| Trạng thái | Mục và mô tả gốc | Nhận xét |
|---|---|---|
| ❔ Can’t tell | **Visual indicator** — A clear representation that content is loading or in progress of change | Ảnh không chụp thời gian chờ; không xác nhận có spinner hoặc skeleton. |
| ❔ Can’t tell | **Text** — Explaining the loading state | Không có nội dung loading trong trạng thái kết quả này; cần state khi gửi. |
| ❔ Can’t tell | **Time** — Determine how long the time between two actions must be to require a loading component | Không thể đo độ trễ từ ảnh. Bản thật cần đo thời gian phản hồi; không thêm chờ giả để trang trí. |
| ❔ Can’t tell | **Accessibility** — Ensure your loading state can be clearly seen | Không thể kiểm tra thông báo cho screen reader, tương phản spinner hay aria-busy bằng concept tĩnh. |
| ⚪ Not needed here | **Visuals** — Entertain the user with an illustration during the loading state | Một phép kiểm tra tin ngắn chỉ cần trạng thái chờ và hướng khôi phục; minh họa giải trí sẽ gây nhiễu buổi demo. |

Các mục chưa thể kết luận cần prototype hoặc trạng thái tương ứng. Ảnh có kết quả không tự cho biết hành vi loading/lỗi.

## Quan sát bổ sung theo bài toán

- Điểm 0,94 có thể bị hiểu là độ chính xác. Thiết kế mới phải giải thích score và threshold, không biến thành “đúng 94%”. Đây là nguy cơ cần kiểm chứng bằng phỏng vấn, chưa phải phát hiện từ người dùng thật.
- Ảnh có người gửi, nút chặn/cho phép và nhãn A. Cần chốt quy tắc xung đột và chứng minh tách biệt A/B bằng phiên/backend thật khi triển khai. Một ảnh hoặc dropdown không đủ chứng minh.
- Giữ phong cách sáng xanh theo lựa chọn người dùng. Mục tiêu kiểm thử là hoàn thành demo và hiểu kết quả, không thêm dashboard vận hành ngoài phạm vi.
