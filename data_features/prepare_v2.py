"""TV1 v2: QA, corpus phát triển theo nhóm, và challenge khóa trước huấn luyện."""
from pathlib import Path
import hashlib
import json
import sys
import pandas as pd
from vi_text_v2 import normalize, redact, VERSION

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'traditional_ml/bo_sung_tv2/vi/data'
OLD=ROOT/'cloud_app/bo_sung_tv4_app/vi_model_revision/data'

TRAIN_HAM='''Con hơi mệt, hôm nay tôi ở nhà chăm con nên xin nghỉ buổi làm.
Em bị cảm nên nhờ đồng nghiệp hỗ trợ ca trực sáng.
Cháu ho nhiều, mẹ xin phép cô cho cháu nghỉ lớp hôm nay.
Vợ tôi vừa ốm nên tôi cần đổi lịch trực để chăm sóc gia đình.
Tôi sẽ làm việc tại nhà vì con đang cần người trông nom.
Sáng nay bé khó chịu trong người, tôi xin dời cuộc hẹn sang ngày khác.
Bạn gom hóa đơn tiền ăn rồi chia đều cho mọi người giúp mình.
Tớ gửi tiền mua sách rồi, lúc rảnh bạn kiểm tra tài khoản nhé.
Chị đã thanh toán tiền điện tháng này, em không cần đóng lại.
Mẹ nhớ nhắc con trả tiền vé xe cho dì nhé.
Tài liệu môn lập trình nằm ở https://drive.google.com/drive/folders/monhoc nhé.
Thầy đưa link bài thực hành ở https://classroom.google.com/c/baitap cho lớp.
Bạn tải đề cương từ https://courses.example.edu.vn/tailieu rồi đọc trước khi tới lớp.
Mình gửi đường dẫn biên bản họp: https://docs.google.com/document/d/bienban.
Đội chúng ta đổi chỗ tập dượt sang phòng hội thảo tầng bốn.
Tớ nhận phần trình bày phương pháp, cậu nói phần kết quả nha.
Để kịp hoàn thành báo cáo, chúng mình nên gặp nhau sau tiết học.
Chiều mai tôi đưa bố đi tái khám, xin phép rời công ty sớm.
Mình bị mất giọng nên hôm nay nhờ bạn trình bày giúp.
Tớ quên mang tiền mặt, cậu trả hộ tiền bữa trưa rồi mình gửi lại nhé.
Đừng gửi mã xác nhận tài khoản cho người tự nhận là công an.
Không chuyển khoản để nhận phần thưởng từ một người không quen biết.
Người gọi yêu cầu đọc mật khẩu là kẻ giả mạo, hãy ngắt cuộc gọi.
Nhân viên hỗ trợ thật không yêu cầu bạn gửi mã OTP qua tin nhắn.
Ai nhờ chuyển tiền gấp qua tài khoản lạ thì cần gọi xác nhận trước.
Nếu được hứa nhận quà nhưng phải trả phí trước, hãy kiểm tra nguồn tin.
Đừng cài tập tin APK trong tin nhắn không rõ người gửi.
Không điền mật khẩu vào trang web được người lạ gửi qua SMS.
Ba đừng chuyển tiền cho ai nói con bị tai nạn khi chưa gọi lại cho con.
Cô giáo thật không yêu cầu phụ huynh nộp tiền vào tài khoản cá nhân qua tin nhắn lạ.
Đề nghị báo ngân hàng khi gặp người đòi mã xác thực để mở khóa tài khoản.
Hãy chặn cuộc gọi tự xưng điều tra viên và không làm theo lệnh chuyển tiền.
Trong bài học, chúng ta phân tích câu quảng cáo vay gấp để nhận diện spam.
Cả đội cần chỉ ra dấu hiệu sai trong lời mời nhận thưởng phải đóng phí.
Bài giảng hôm nay dùng ví dụ yêu cầu gửi mật khẩu để minh họa lừa đảo.
Tôi vừa báo cáo đường link giả mạo sau khi được yêu cầu điền OTP.
Hôm trước có người mời đầu tư chắc lãi, tôi đã từ chối và cảnh báo gia đình.
Chủ đề báo cáo là cách bảo vệ tài khoản trước tin nhắn giả ngân hàng.
Con đọc bài cảnh báo việc nhẹ lương cao rồi kể cho ông bà nghe nhé.
Chúng ta phải giải thích vì sao nạp tiền để nhận hoa hồng có thể là lừa đảo.
'''
TRAIN_SPAM='''Hãy gửi mã xác nhận tài khoản cho nhân viên hỗ trợ để mở khóa giao dịch.
Gửi mật khẩu và mã OTP tới người xác minh để nhận tiền hoàn lại ngay.
Chuyển khoản vào tài khoản lạ này để nhận giải thưởng bạn vừa trúng.
Nhập thông tin đăng nhập ngân hàng tại https://bao-ve-khan.example để tránh mất tiền.
Đây là công an điều tra, chuyển ngay tiền tiết kiệm sang tài khoản an toàn này.
Con bạn đang cấp cứu, chuyển tiền vào tài khoản cá nhân ngay và không gọi lại.
Giáo viên yêu cầu phụ huynh nộp tiền cứu trợ gấp vào tài khoản riêng để giữ suất học.
Hãy cài file APK ở https://xac-nhan-dan-cu.example rồi gửi mã OTP cho người hướng dẫn.
Nhân viên ngân hàng cần bạn đọc mật khẩu để đối chiếu hồ sơ nhận thưởng.
Nếu không gửi mã xác thực trong hôm nay, tài khoản sẽ bị đóng vĩnh viễn.
Nộp khoản phí nhận quà trước để được giao phần thưởng giá trị lớn.
Thanh toán lệ phí rút tiền vào ví cá nhân này để được mở khóa số dư.
Việc làm nhẹ nhàng lương cao, chuyển tiền đặt cọc trước khi nhận công việc.
Tuyển người làm đơn hàng nhận hoa hồng, nạp tiền trước để có nhiệm vụ.
Đăng ký khoản vay tức thì không cần tài sản tại https://vay-tuc-thi.example.
Hỗ trợ vay nóng cho mọi đối tượng, duyệt nhanh và giải ngân ngay hôm nay.
Nạp tiền chơi casino nhận thưởng lớn, truy cập https://game-nhan-thuong.example.
Nhà cái hoàn tiền thua cược, mở tài khoản và nạp lần đầu để nhận quà.
Đầu tư bảo đảm lãi cao mỗi ngày, chuyển vốn để tham gia nhóm kín.
Tham dự lớp kiếm tiền bảo đảm nhân đôi vốn, nộp phí đăng ký ngay.
Buổi hướng dẫn làm giàu chỉ nhận người đã nạp vốn vào quỹ lợi nhuận.
Mời tham gia nhóm tài chính cam kết lợi nhuận cố định không rủi ro.
Mua hàng ngay tại https://giam-soc.example để nhận tiền thưởng đặc biệt.
Bạn được chọn nhận phiếu thưởng miễn phí, chuyển phí kích hoạt để lấy quà.
Nhân viên bưu điện thông báo quà bất ngờ, yêu cầu trả tiền bảo hiểm trước.
Hoàn tiền trợ cấp: gửi mật khẩu tài khoản để được xác thực danh sách nhận tiền.
Thông báo tiền điện bị truy thu, chuyển vào tài khoản cá nhân để tránh cắt điện.
Tài khoản ví điện tử có lỗi, cung cấp mã OTP qua đường link hỗ trợ này ngay.
Chúc mừng bạn có khoản thưởng lớn, gửi số thẻ cùng mật khẩu để lĩnh giải.
Không cần đi làm vẫn có thu nhập, đóng phí thành viên để nhận tiền hàng ngày.
'''
VAL_HAM='''Con đang mệt nên tôi xin chuyển buổi làm sang trực tuyến.
Nhờ cậu tính tiền bữa ăn rồi báo lại phần mỗi người.
Slide để bảo vệ đề tài đã gửi vào https://drive.google.com/file/d/slidethuyettrinh nhé.
Đừng đọc mã OTP cho người tự xưng nhân viên hỗ trợ.
Tôi không đồng ý chuyển tiền nhận quà, đây có vẻ là một trò lừa đảo.
Hãy gọi ngân hàng qua số chính thức khi ai đó đòi mật khẩu.
Thầy nhờ phân tích ví dụ giả mạo công an yêu cầu gửi tiền trong bài thực hành.
Mẹ đang chờ khám nên chiều nay tôi xin phép về trễ.
Hôm qua tôi gặp tin nhắn lừa nhận thưởng, đã bỏ qua và báo cáo.
Lớp sẽ đọc tài liệu ở https://learning.example.edu.vn/nhom trước buổi trao đổi.
Không cài ứng dụng do người gọi số lạ yêu cầu cài đặt.
Em mượn tiền mua vé xem phim, cuối tuần em trả lại anh nhé.
'''
VAL_SPAM='''Gửi mã OTP cho tư vấn viên để cập nhật hạn mức thẻ ngay hôm nay.
Bạn phải chuyển phí hồ sơ trước mới được nhận khoản tiền thưởng đã công bố.
Chuyển vốn vào nhóm cam kết lãi ngày để được nhận lợi nhuận đều đặn.
Mời vay tiền không cần xác minh thu nhập, truy cập https://ho-tro-von.example.
Tải ứng dụng ở đường link lạ này rồi cung cấp mật khẩu ngân hàng để xác thực cư trú.
Giả sử bạn muốn kiếm tiền nhanh, hãy nạp tiền vào nhà cái để nhận thưởng.
Mở khóa tài khoản bằng cách gửi mã xác nhận đăng nhập cho người hướng dẫn.
Lương rất cao cho công việc tại nhà, cần nộp tiền kích hoạt trước khi làm.
Bạn có quà tặng lớn, thanh toán tiền vận chuyển qua tài khoản cá nhân ngay.
Tài khoản an toàn do điều tra viên cung cấp: hãy chuyển toàn bộ tiền tiết kiệm tới đây.
Cam kết hoàn lại gấp đôi số tiền đặt cọc cho buổi học làm giàu này.
Ưu đãi mua sắm độc quyền, bấm https://mua-ngay.example để nhận quà thưởng.
'''
CHALLENGE_HAM='''Lát nữa tổ mình gặp ở phòng đọc để ráp các phần báo cáo lại với nhau.
Nhờ em gửi ảnh bảng phân công cho mấy bạn vắng tiết sáng nay.
Tôi xin làm ca tối thay vì ca sáng để đưa cháu đi kiểm tra sức khỏe.
Mình ứng tiền mua đồ ăn cho cả tổ, cuối buổi mọi người chia lại nhé.
Chiều thứ tư mình cùng luyện phần trả lời phản biện ở hội trường nhé.
Bạn đưa ông tới bệnh viện xong thì báo mình biết với nha.
Hãy bỏ qua tin nhắn đòi mật khẩu để nhận trợ cấp, đó là dấu hiệu giả mạo.
Không ai được yêu cầu đọc mã bảo mật của bạn qua cuộc gọi cả.
Nếu người gọi đòi nộp tiền cứu con, hãy bình tĩnh gọi cho con kiểm chứng.
Link bài đọc trên lớp: https://docs.google.com/document/d/baidocmonhoc.
Tớ để bài tập trong https://drive.google.com/drive/folders/baiham, bạn mở xem nhé.
Đây là địa chỉ trang môn học https://study.example.edu.vn/sinhvien để tra thời khóa biểu.
Tụi mình sẽ góp ý nội dung trước rồi mới sửa giao diện slide.
Bà đang nhức đầu nên mình ghé nhà mua thuốc cho bà trước khi tới lớp.
Anh đã gửi lại tiền vé tàu, em kiểm tra lúc nào tiện nhé.
Cháu không khỏe nên gia đình xin nghỉ buổi sinh hoạt hôm nay.
Học sinh được yêu cầu nhận xét câu dụ nạp tiền trong bài phòng chống lừa đảo.
Mình đã từ chối lời mời vay lãi thấp từ một số máy không quen.
Đừng gửi ảnh thẻ và mật khẩu khi người lạ hứa hoàn phí bảo hiểm.
Tôi muốn hỏi phòng nhân sự thủ tục xin nghỉ để chăm người thân bị bệnh.
Ban quản trị nhắc cư dân không đưa mã cửa cho người giao hàng lạ.
Cô đã trả lại bản báo cáo và muốn nhóm bổ sung phần thảo luận.
Nhớ cắm sạc máy trước khi tới buổi trình diễn sản phẩm.
Đọc tài liệu hướng dẫn cách phát hiện link giả rồi ghi ý chính vào vở nhé.
'''
CHALLENGE_SPAM='''Hãy điền mã bảo mật và mật khẩu vào https://doi-soat-nhanh.example để tránh đình chỉ tài khoản.
Bạn đang có phần thưởng bằng tiền, chuyển phí nhận giải ngay để giữ quyền nhận.
Một dự án chắc lãi đang nhận người góp vốn, chuyển tiền ngay để nhân ba số dư.
Làm vài thao tác online là có lương cao, nộp phí công cụ để được nhận việc.
Mời nạp tiền tại https://nhacai-uu-dai.example để nhận hoàn cược mỗi ngày.
Khoản vay được duyệt sẵn không yêu cầu chứng minh tài sản, đăng ký nhận tiền ngay.
Chúng tôi cần mật khẩu ví điện tử để kích hoạt trợ cấp cho bạn trong hôm nay.
Chuyển tiền đến tài khoản của cán bộ xác minh để chứng minh bạn không liên quan vụ án.
Phần quà bất ngờ đang trên đường giao, hãy nộp lệ phí bảo hiểm trước khi nhận.
Lớp đầu tư bảo đảm lợi tức gấp đôi chỉ nhận học viên đã nộp cọc vào quỹ.
Nhà tuyển dụng yêu cầu nạp tiền trước để mở thêm đơn hàng có hoa hồng cao.
Thuê bao được thưởng gói tiền mặt, gửi số thẻ và mật khẩu để hoàn tất xác nhận.
Vay vốn chấp nhận mọi lịch sử tín dụng, truy cập https://vay-giai-ngan.example ngay.
Xem hướng dẫn nhận quà ở https://thuong-hap-dan.example và đóng phí hồ sơ để lĩnh tiền.
Bạn phải đọc mã OTP cho người hỗ trợ qua cuộc gọi để được bỏ chặn giao dịch.
Nộp tiền để giữ chỗ trong nhóm kinh doanh cam kết lợi nhuận mỗi giờ.
Phiếu thưởng mua sắm trúng ngẫu nhiên, thanh toán tiền xác nhận để kích hoạt quyền lợi.
Hãy chuyển tiền khám cấp cứu cho con vào tài khoản này ngay, không được gọi điện kiểm chứng.
Tải tập tin APK xác thực thuế từ đường dẫn này rồi nhập mật khẩu ngân hàng để hoàn tất.
Bạn có khoản tiền bị treo, nộp phí vào ví cá nhân của chuyên viên để mở lệnh rút.
Tham gia casino đang ưu đãi tiền nạp, thắng thưởng rồi rút tiền siêu nhanh.
Mua bộ tài liệu làm giàu kèm gói vốn đầu tư để nhận cam kết lãi chắc chắn.
Chủ tài khoản sẽ bị phạt nếu không gửi mã đăng nhập cho nhân viên thanh tra ngay.
Được tặng vé xe miễn phí nhưng phải chuyển tiền kích hoạt vào tài khoản người tổ chức trước.
'''


def rows_from(text,label,role):
    return [dict(id=f'v2-{role}-{label}-{i:03}',text=redact(line.strip()),y=label,
                 group=f'authored-{role}-{label}-{i:03}',source='assistant-authored-v2',review_status='author-labelled-not-human-validated')
            for i,line in enumerate(text.strip().splitlines()) if line.strip()]


def main():
    (HERE/'data').mkdir(parents=True,exist_ok=True);(HERE/'reports').mkdir(exist_ok=True)
    frames={s:pd.read_csv(SOURCE/f'{s}.csv') for s in ('train','val','test')}
    for role,frame in frames.items():
        frame['group']=[f'source-{role}-{i}' for i in frame.id];frame['source']='published-corpus'
        frame['review_status']='publisher-label-inherited'
    for role,file in [('train','train_authored.csv'),('val','validation_authored.csv')]:
        extra=pd.read_csv(OLD/file);extra['source']='assistant-authored-v1';extra['group']=extra.id
        extra['review_status']='author-labelled-not-human-validated';frames[role]=pd.concat([frames[role],extra],ignore_index=True)
    for role,ham,spam in [('train',TRAIN_HAM,TRAIN_SPAM),('val',VAL_HAM,VAL_SPAM)]:
        extra=pd.DataFrame(rows_from(ham,0,role)+rows_from(spam,1,role))
        frames[role]=pd.concat([frames[role],extra],ignore_index=True)
    challenge=pd.DataFrame(rows_from(CHALLENGE_HAM,0,'challenge')+rows_from(CHALLENGE_SPAM,1,'challenge'))
    # Các câu phát triển đã từng xem giữ làm regression, không chuyển vào train/val.
    known=json.loads((ROOT/'cloud_app/bo_sung_tv4_app/tests/vi_semantic_cases.json').read_text(encoding='utf-8'))
    newer=json.loads((ROOT.parent/'output/reports/tv4_retest/new_semantic_cases.json').read_text(encoding='utf-8'))
    regression=pd.DataFrame([dict(id=f'regression-{i}',text=r['text'],y=int(r['label']=='spam'),group=f'regression-{i}',source='seen-development-regression',review_status='author-labelled-not-human-validated') for i,r in enumerate(known+newer)])
    for frame in list(frames.values())+[challenge,regression]:
        frame['text']=frame.text.map(redact);frame['input_key']=frame.text.map(normalize)
    all_dev=pd.concat([frames['train'],frames['val']]);conflicts=set(all_dev.groupby('input_key').y.nunique().loc[lambda n:n>1].index)
    removed=[]
    for split in ('val','train'):
        frame=frames[split]
        forbidden=set(frames['test'].input_key)|set(challenge.input_key)|set(regression.input_key)|conflicts
        if split=='train':forbidden |= set(frames['val'].input_key)
        bad=frame.input_key.isin(forbidden)
        removed.append(frame[bad].assign(excluded_from=split,reason='normalized overlap or conflicting label'))
        frames[split]=frame[~bad].drop_duplicates('input_key').reset_index(drop=True)
    assert not set(frames['train'].input_key)&set(frames['val'].input_key)
    assert not set(challenge.input_key)&set(pd.concat([frames['train'],frames['val'],regression]).input_key)
    for name,frame in {**frames,'challenge':challenge,'regression':regression}.items():
        frame.to_csv(HERE/f'data/{name}.csv',index=False)
    quarantine=pd.concat(removed,ignore_index=True);quarantine.to_csv(HERE/'reports/excluded.csv',index=False)
    # Accent/no-accent variants share the same ID/family and are evaluated, never split as unrelated rows.
    manifest=dict(preprocessing=VERSION,source_manifest='data_features/bo_sung_tv1/manifest.json',
                  counts={name:{'rows':len(f),'ham':int(f.y.eq(0).sum()),'spam':int(f.y.eq(1).sum())} for name,f in {**frames,'challenge':challenge,'regression':regression}.items()},
                  input_hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'train.csv',SOURCE/'val.csv',SOURCE/'test.csv',OLD/'train_authored.csv',OLD/'validation_authored.csv']},
                  files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'data').glob('*.csv'))},
                  label_conflict_groups=len(conflicts),excluded_rows=len(quarantine),
                  provenance='Published corpus inherited + labelled synthetic development coverage. No new human-verified SMS available; user confirmed. Challenge frozen before fitting, authored by the same assistant, not independent real-world validation.',
                  label_policy={'ham':'ordinary conversation, user-requested transactional notices, safety warnings and educational examples','spam':'unsolicited promotion, credential/OTP requests, advance-fee or guaranteed-return solicitations'},
                  compatibility='Original test retained unchanged in text/label; source code and prior artifact packages not overwritten.')
    manifest['dataset_id']='vi-tv1-v2-'+hashlib.sha256(json.dumps(manifest['files_sha256'],sort_keys=True).encode()).hexdigest()[:12]
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest['counts'],ensure_ascii=False,indent=2));print('Excluded',len(quarantine),'conflicts',len(conflicts),'dataset',manifest['dataset_id'])


if __name__=='__main__':main()
