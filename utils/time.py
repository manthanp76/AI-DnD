from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from calendar import monthrange

class TimeScale(Enum):
    ROUND = "round"  # 6 seconds
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

@dataclass
class GameTime:
    timestamp: datetime
    round_counter: int = 0
    
    def advance(self, amount: int, scale: TimeScale) -> None:
        """Advance game time with accurate calendar calculations"""
        if scale == TimeScale.ROUND:
            self.round_counter += amount
            self.timestamp += timedelta(seconds=amount * 6)
        else:
            if scale == TimeScale.MINUTE:
                delta = timedelta(minutes=amount)
            elif scale == TimeScale.HOUR:
                delta = timedelta(hours=amount)
            elif scale == TimeScale.DAY:
                delta = timedelta(days=amount)
            elif scale == TimeScale.WEEK:
                delta = timedelta(weeks=amount)
            elif scale == TimeScale.MONTH:
                # Accurate month calculation
                months = amount
                new_month = self.timestamp.month + months
                years = (new_month - 1) // 12
                final_month = ((new_month - 1) % 12) + 1
                final_year = self.timestamp.year + years
                
                # Adjust for month lengths
                max_days = monthrange(final_year, final_month)[1]
                final_day = min(self.timestamp.day, max_days)
                
                self.timestamp = self.timestamp.replace(
                    year=final_year,
                    month=final_month,
                    day=final_day
                )
            elif scale == TimeScale.YEAR:
                self.timestamp = self.timestamp.replace(
                    year=self.timestamp.year + amount
                )
            
            # Update round counter
            total_seconds = (self.timestamp - self.timestamp).total_seconds()
            self.round_counter += int(total_seconds / 6)

class TimeManager:
    def __init__(self, start_time: Optional[datetime] = None):
        self.game_time = GameTime(start_time or datetime.now())
        self.time_triggers: Dict[datetime, List[Tuple[Callable, str]]] = {}
        self.persistent_effects: List[Dict] = []
        self._lock = asyncio.Lock()

    async def advance_time(self, amount: int, scale: TimeScale) -> List[Dict]:
        """Thread-safe time advancement"""
        async with self._lock:
            old_time = self.game_time.timestamp
            self.game_time.advance(amount, scale)
            
            triggered_effects = await self._process_time_triggers(old_time)
            effect_updates = await self._update_persistent_effects()
            
            return triggered_effects + effect_updates
        
    def get_state(self) -> Dict[str, Any]:
        return {
            'current_time': self.game_time.timestamp.isoformat(),
            'round_counter': self.game_time.round_counter,
            'triggers': [
                {
                    'time': t.isoformat(),
                    'trigger_id': tid
                } for t, (_, tid) in self.time_triggers.items()
            ]
        }

    async def add_time_trigger(self, 
                             trigger_time: datetime,
                             callback: Callable,
                             trigger_id: str) -> None:
        """Add a trigger with unique identifier"""
        async with self._lock:
            if trigger_time not in self.time_triggers:
                self.time_triggers[trigger_time] = []
            self.time_triggers[trigger_time].append((callback, trigger_id))

    async def remove_time_trigger(self, trigger_id: str) -> None:
        """Remove a specific trigger by ID"""
        async with self._lock:
            for time, triggers in self.time_triggers.items():
                self.time_triggers[time] = [
                    (cb, tid) for cb, tid in triggers if tid != trigger_id
                ]

    async def _process_time_triggers(self, old_time: datetime) -> List[Dict]:
        """Process triggers in a thread-safe manner"""
        triggered = []
        
        async with self._lock:
            times_to_process = [t for t in self.time_triggers.keys()
                              if old_time < t <= self.game_time.timestamp]
            
            for trigger_time in sorted(times_to_process):
                for callback, trigger_id in self.time_triggers[trigger_time]:
                    try:
                        result = await callback()
                        triggered.append({
                            'time': trigger_time,
                            'type': 'trigger',
                            'id': trigger_id,
                            'result': result
                        })
                    except Exception as e:
                        logging.error(f"Error processing trigger {trigger_id}: {e}")
                        
            # Clean up processed triggers
            for time in times_to_process:
                del self.time_triggers[time]
                
        return triggered
