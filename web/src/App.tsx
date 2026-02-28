import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { HomeScreen } from './screens/HomeScreen';
import { GameScreen } from './screens/GameScreen';
import { GalleryScreen } from './screens/GalleryScreen';
import { DeckScreen } from './screens/DeckScreen';
import './App.css';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="app">
        {/* ナビゲーションバー */}
        <nav className="app-nav">
          <Link to="/" className="nav-logo">
            Pixel Simulation Arena
          </Link>
          <div className="nav-links">
            <Link to="/game" className="nav-link">
              ゲーム
            </Link>
            <Link to="/gallery" className="nav-link">
              ギャラリー
            </Link>
            <Link to="/deck" className="nav-link">
              デッキ編成
            </Link>
          </div>
        </nav>

        {/* ルーティング */}
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/game" element={<GameScreen />} />
          <Route path="/gallery" element={<GalleryScreen />} />
          <Route path="/deck" element={<DeckScreen />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
};
