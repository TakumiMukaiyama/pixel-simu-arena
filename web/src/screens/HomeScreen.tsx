import { Link } from 'react-router-dom';
import './HomeScreen.css';

export const HomeScreen: React.FC = () => {
  return (
    <div className="home-screen">
      <div className="home-content">
        <h1 className="home-title">Pixel Simulation Arena</h1>
        <p className="home-subtitle">リアルタイム1レーンバトル</p>

        <nav className="home-nav">
          <Link to="/game" className="nav-button primary">
            <span className="button-icon">⚔️</span>
            <span className="button-text">ゲームを開始</span>
          </Link>

          <Link to="/gallery" className="nav-button">
            <span className="button-icon">📖</span>
            <span className="button-text">ギャラリー</span>
          </Link>

          <Link to="/deck" className="nav-button">
            <span className="button-icon">🎴</span>
            <span className="button-text">デッキ編成</span>
          </Link>
        </nav>

        <div className="home-info">
          <div className="info-card">
            <h3>ゲームルール</h3>
            <ul>
              <li>1レーンでのリアルタイムバトル</li>
              <li>コストを貯めてユニットを召喚</li>
              <li>相手の拠点を破壊すれば勝利</li>
              <li>5体のデッキでAIと対戦</li>
            </ul>
          </div>

          <div className="info-card">
            <h3>操作方法</h3>
            <ul>
              <li>デッキカードをクリックで召喚</li>
              <li>コストは時間経過で自動回復</li>
              <li>ユニットは自動で移動・攻撃</li>
              <li>戦略的にユニットを配置</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
