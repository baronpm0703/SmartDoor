Add faceid check theo account - 1 ng 1 ảnh

kịch bản
+ Khi Người dùng đăng ký, sẽ tạo 1 collect trong firestore chứa email, UID, username = email (default).
=> Cái title sẽ luôn là welcome Username.
+ Khi 1 ng nào đó xác nhận khuôn mặt, dataFaceID có => sẽ hiển thị ra Visitor 
+ Ngược lại k có => stranger alert
? vấn đề là nếu lm sao xác nhận chủ nhà ( ng đang đăng nhập vào web ). Cách thức check faceID như thế nào?


flow => đăng ký tạo 1 document mới theo UID + các info username, UID, email, url bị trống
đăng nhập vào => có chỉnh sửa username + up thêm ảnh vào url
upload đc call => up file mới lên với tên file = UID => get đường dẫn down load đó



Cần làm: sửa nút lưu, chỉnh lại UI