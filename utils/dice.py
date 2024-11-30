# utils/dice.py
from typing import List, Tuple, Optional
import random
from dataclasses import dataclass

@dataclass
class DiceRoll:
    dice_type: int
    count: int
    modifier: int = 0
    results: List[int] = None
    total: int = None
    is_critical: bool = False
    is_fumble: bool = False

class DiceRoller:
    @staticmethod
    def roll(dice_str: str) -> DiceRoll:
        """Roll dice (e.g., "1d6+2", "2d8-1")"""
        try:
            # Parse the dice string
            modifier = 0
            if '+' in dice_str:
                dice_part, mod = dice_str.split('+')
                modifier = int(mod)
            elif '-' in dice_str:
                dice_part, mod = dice_str.split('-')
                modifier = -int(mod)
            else:
                dice_part = dice_str

            # Parse dice count and type
            if 'd' in dice_part:
                count, sides = dice_part.split('d')
                count = int(count) if count else 1
                sides = int(sides)
            else:
                raise ValueError("Invalid dice format")

            # Roll the dice
            results = [random.randint(1, sides) for _ in range(count)]
            total = sum(results) + modifier

            # Check for critical roll (all max values) or fumble (all 1s)
            is_critical = all(r == sides for r in results)
            is_fumble = all(r == 1 for r in results)

            return DiceRoll(
                dice_type=sides,
                count=count,
                modifier=modifier,
                results=results,
                total=total,
                is_critical=is_critical,
                is_fumble=is_fumble
            )
            
        except Exception as e:
            # Fallback to simple d6 roll
            result = random.randint(1, 6)
            return DiceRoll(
                dice_type=6,
                count=1,
                results=[result],
                total=result
            )

    @staticmethod
    def skill_check(difficulty: str = "normal") -> Tuple[bool, int]:
        """Perform a skill check with different difficulty levels"""
        roll = DiceRoller.roll("1d20")
        
        # Difficulty thresholds
        thresholds = {
            "very_easy": 5,
            "easy": 10,
            "normal": 15,
            "hard": 20,
            "very_hard": 25
        }
        
        threshold = thresholds.get(difficulty, 15)
        success = roll.total >= threshold
        
        # Critical success/failure override normal results
        if roll.is_critical:
            success = True
        elif roll.is_fumble:
            success = False
            
        return success, roll.total

    @staticmethod
    def get_roll_description(roll: DiceRoll) -> str:
        """Get a detailed description of roll results"""
        parts = [f"Rolled {roll.count}d{roll.dice_type}"]
        
        if roll.modifier != 0:
            mod_sign = '+' if roll.modifier > 0 else ''
            parts.append(f"{mod_sign}{roll.modifier}")
            
        parts.append(f"-> {roll.results}")
        
        if roll.modifier != 0:
            parts.append(f"({sum(roll.results)} {'+' if roll.modifier > 0 else ''}{roll.modifier})")
            
        parts.append(f"= {roll.total}")
        
        if roll.is_critical:
            parts.append("(Critical Success!)")
        elif roll.is_fumble:
            parts.append("(Critical Failure!)")
            
        return " ".join(parts)

    @staticmethod
    def advantage_roll(dice_str: str) -> DiceRoll:
        """Roll with advantage (take higher of two rolls)"""
        roll1 = DiceRoller.roll(dice_str)
        roll2 = DiceRoller.roll(dice_str)
        return roll1 if roll1.total > roll2.total else roll2

    @staticmethod
    def disadvantage_roll(dice_str: str) -> DiceRoll:
        """Roll with disadvantage (take lower of two rolls)"""
        roll1 = DiceRoller.roll(dice_str)
        roll2 = DiceRoller.roll(dice_str)
        return roll1 if roll1.total < roll2.total else roll2
