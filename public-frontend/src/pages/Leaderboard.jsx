import { useState, useEffect } from 'react'
import { Trophy, Users, Award } from 'lucide-react'
import { api } from '../App'

export default function Leaderboard() {
  const [leaders, setLeaders] = useState([])

  useEffect(() => {
    api.get('/public/leaderboard?limit=20').then(r => setLeaders(r.data)).catch(console.error)
  }, [])

  const medals = ['🥇', '🥈', '🥉']

  return (
    <div className="mt-4 space-y-6 max-w-2xl mx-auto">
      <div className="text-center animate-in">
        <div className="inline-flex p-3 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 mb-3">
          <Trophy size={32} className="text-amber-400" />
        </div>
        <h2 className="text-3xl font-black text-white">Community Leaderboard</h2>
        <p className="text-sm text-gray-500 mt-2">Districts ranked by citizen road safety contributions</p>
      </div>

      <div className="glass-card overflow-hidden animate-in" style={{ animationDelay: '200ms' }}>
        {leaders.map((l, i) => (
          <div key={i} className={`flex items-center justify-between p-4 hover:bg-white/[0.03] transition-colors ${i < leaders.length - 1 ? 'border-b border-white/5' : ''}`}>
            <div className="flex items-center gap-4">
              <div className="w-8 text-center">
                {i < 3 ? <span className="text-xl">{medals[i]}</span> : <span className="text-sm text-gray-600 font-mono">{i + 1}</span>}
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{l.district}</p>
                <p className="text-xs text-gray-500 flex items-center gap-1"><Users size={10} />{l.contributors} contributor{l.contributors !== 1 ? 's' : ''}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-amber-300">{l.total_points?.toLocaleString()}</p>
              <p className="text-[10px] text-gray-500 uppercase tracking-wide">points</p>
            </div>
          </div>
        ))}
        {leaders.length === 0 && (
          <div className="p-8 text-center">
            <Award size={40} className="text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500">No community reports yet — be the first!</p>
          </div>
        )}
      </div>
    </div>
  )
}
