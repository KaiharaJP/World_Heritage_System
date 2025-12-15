# World_Heritage_System
## 起動方法
rootのフォルダ内で以下のコマンドを打つと、backendが起動する
uvicorn backend.app.main:app --reload

frontendフォルダ内で、以下のコマンドを打つと、fronendが起動する
以下のコマンドを実行する
cd frontend
Set-ExecutionPolicy RemoteSigned -Scope Process -Force
npm run dev

その後、以下のURLにアクセス
http://localhost:3000

# コマンド
## バックエンドの起動方法
1. cd .\World_Heritage_System\
2. uvicorn backend.app.main:app --reload

## フロントエンドの起動方法
1. cd .\World_Heritage_System\
2. cd frontend
3. Set-ExecutionPolicy RemoteSigned -Scope Process -Force
4. npm run dev