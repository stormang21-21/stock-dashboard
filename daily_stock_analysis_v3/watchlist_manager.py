"""
Watchlist Management System

Manage stock watchlists with real-time tracking.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class WatchlistStock:
    """Stock in a watchlist"""
    symbol: str
    company_name: str = ''
    added_at: str = ''
    notes: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'company_name': self.company_name,
            'added_at': self.added_at,
            'notes': self.notes,
        }


@dataclass
class Watchlist:
    """User watchlist"""
    id: str
    name: str
    user_id: str
    stocks: List[WatchlistStock]
    created_at: str = ''
    updated_at: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'stocks': [s.to_dict() for s in self.stocks],
            'stocks_count': len(self.stocks),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class WatchlistManager:
    """Manage user watchlists"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.watchlists: Dict[str, Watchlist] = {}
        self.user_watchlists: Dict[str, List[str]] = {}  # user_id -> [watchlist_ids]
    
    def create_watchlist(self, user_id: str, name: str = "My Watchlist") -> Watchlist:
        """Create a new watchlist"""
        watchlist_id = f"wl_{datetime.now().timestamp()}"
        now = datetime.now().isoformat()
        
        watchlist = Watchlist(
            id=watchlist_id,
            name=name,
            user_id=user_id,
            stocks=[],
            created_at=now,
            updated_at=now,
        )
        
        self.watchlists[watchlist_id] = watchlist
        
        if user_id not in self.user_watchlists:
            self.user_watchlists[user_id] = []
        self.user_watchlists[user_id].append(watchlist_id)
        
        logger.info(f"Created watchlist {watchlist_id} for {user_id}")
        return watchlist
    
    def delete_watchlist(self, user_id: str, watchlist_id: str) -> bool:
        """Delete a watchlist"""
        if watchlist_id not in self.watchlists:
            return False
        
        watchlist = self.watchlists[watchlist_id]
        if watchlist.user_id != user_id:
            return False
        
        del self.watchlists[watchlist_id]
        if user_id in self.user_watchlists:
            if watchlist_id in self.user_watchlists[user_id]:
                self.user_watchlists[user_id].remove(watchlist_id)
        
        logger.info(f"Deleted watchlist {watchlist_id}")
        return True
    
    def add_stock(self, user_id: str, watchlist_id: str, symbol: str, company_name: str = '', notes: str = '') -> bool:
        """Add stock to watchlist"""
        if watchlist_id not in self.watchlists:
            return False
        
        watchlist = self.watchlists[watchlist_id]
        if watchlist.user_id != user_id:
            return False
        
        # Check if already in watchlist
        if any(s.symbol == symbol.upper() for s in watchlist.stocks):
            return False
        
        watchlist.stocks.append(WatchlistStock(
            symbol=symbol.upper(),
            company_name=company_name,
            added_at=datetime.now().isoformat(),
            notes=notes,
        ))
        watchlist.updated_at = datetime.now().isoformat()
        
        logger.info(f"Added {symbol} to watchlist {watchlist_id}")
        return True
    
    def remove_stock(self, user_id: str, watchlist_id: str, symbol: str) -> bool:
        """Remove stock from watchlist"""
        if watchlist_id not in self.watchlists:
            return False
        
        watchlist = self.watchlists[watchlist_id]
        if watchlist.user_id != user_id:
            return False
        
        watchlist.stocks = [s for s in watchlist.stocks if s.symbol != symbol.upper()]
        watchlist.updated_at = datetime.now().isoformat()
        
        logger.info(f"Removed {symbol} from watchlist {watchlist_id}")
        return True
    
    def get_watchlist(self, user_id: str, watchlist_id: str) -> Optional[Watchlist]:
        """Get a specific watchlist"""
        if watchlist_id not in self.watchlists:
            return None
        
        watchlist = self.watchlists[watchlist_id]
        if watchlist.user_id != user_id:
            return None
        
        return watchlist
    
    def get_user_watchlists(self, user_id: str) -> List[Watchlist]:
        """Get all watchlists for a user"""
        if user_id not in self.user_watchlists:
            return []
        
        return [
            self.watchlists[wl_id]
            for wl_id in self.user_watchlists[user_id]
            if wl_id in self.watchlists
        ]
    
    def update_stock_prices(self, watchlist: Watchlist, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Update prices for all stocks in watchlist"""
        stocks_with_prices = []
        
        for stock in watchlist.stocks:
            stock_data = stock.to_dict()
            if stock.symbol in prices:
                stock_data['current_price'] = prices[stock.symbol]
            else:
                stock_data['current_price'] = 0
            
            stocks_with_prices.append(stock_data)
        
        return stocks_with_prices


# Singleton instance
watchlist_manager = WatchlistManager()


def get_watchlist_manager() -> WatchlistManager:
    """Get watchlist manager instance"""
    return watchlist_manager
