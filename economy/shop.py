"""
Shop system for purchasing items and boosts
"""

from typing import Dict, List, Optional
from database.models import SHOP_ITEMS, ShopItem
from database.database import DatabaseManager
import json

class ShopManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.items = SHOP_ITEMS
    
    def get_shop_items(self, category: str = None) -> Dict[str, ShopItem]:
        """Get shop items, optionally filtered by category"""
        if category:
            return {k: v for k, v in self.items.items() if v.category == category}
        return self.items
    
    def get_item(self, item_id: str) -> Optional[ShopItem]:
        """Get specific shop item"""
        return self.items.get(item_id)
    
    async def get_user_items(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Get user's inventory"""
        inventory = {}
        async with self.db.connection.execute(
            "SELECT item_id, quantity FROM user_items WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                inventory[row[0]] = row[1]
        return inventory
    
    async def add_user_item(self, user_id: int, guild_id: int, item_id: str, quantity: int = 1):
        """Add item to user's inventory"""
        # Check if user already has this item
        async with self.db.connection.execute(
            "SELECT quantity FROM user_items WHERE user_id = ? AND guild_id = ? AND item_id = ?",
            (user_id, guild_id, item_id)
        ) as cursor:
            row = await cursor.fetchone()
        
        if row:
            # Update existing item
            await self.db.connection.execute(
                "UPDATE user_items SET quantity = quantity + ? WHERE user_id = ? AND guild_id = ? AND item_id = ?",
                (quantity, user_id, guild_id, item_id)
            )
        else:
            # Add new item
            await self.db.connection.execute(
                "INSERT INTO user_items (user_id, guild_id, item_id, quantity) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, item_id, quantity)
            )
        
        await self.db.connection.commit()
    
    async def remove_user_item(self, user_id: int, guild_id: int, item_id: str, quantity: int = 1) -> bool:
        """Remove item from user's inventory"""
        async with self.db.connection.execute(
            "SELECT quantity FROM user_items WHERE user_id = ? AND guild_id = ? AND item_id = ?",
            (user_id, guild_id, item_id)
        ) as cursor:
            row = await cursor.fetchone()
        
        if not row or row[0] < quantity:
            return False
        
        new_quantity = row[0] - quantity
        if new_quantity <= 0:
            # Remove item completely
            await self.db.connection.execute(
                "DELETE FROM user_items WHERE user_id = ? AND guild_id = ? AND item_id = ?",
                (user_id, guild_id, item_id)
            )
        else:
            # Update quantity
            await self.db.connection.execute(
                "UPDATE user_items SET quantity = ? WHERE user_id = ? AND guild_id = ? AND item_id = ?",
                (new_quantity, user_id, guild_id, item_id)
            )
        
        await self.db.connection.commit()
        return True
    
    async def purchase_item(self, user_id: int, guild_id: int, item_id: str, quantity: int = 1) -> Dict:
        """Purchase item from shop"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "message": "Item not found in shop"}
        
        # Check max quantity limit
        if item.max_quantity > 0:
            current_quantity = (await self.get_user_items(user_id, guild_id)).get(item_id, 0)
            if current_quantity + quantity > item.max_quantity:
                return {
                    "success": False, 
                    "message": f"You can only own {item.max_quantity} of this item (you have {current_quantity})"
                }
        
        total_cost = item.price * quantity
        
        # Check if user can afford it
        user = await self.db.get_user(user_id, guild_id)
        if not user or user[item.currency_type] < total_cost:
            currency_name = "coins" if item.currency_type == "balance" else "gems"
            return {
                "success": False, 
                "message": f"You need {total_cost} {currency_name} but only have {user[item.currency_type] if user else 0}"
            }
        
        # Process purchase
        await self.db.update_user_balance(user_id, guild_id, -total_cost, item.currency_type)
        await self.add_user_item(user_id, guild_id, item_id, quantity)
        
        currency_name = "coins" if item.currency_type == "balance" else "gems"
        return {
            "success": True,
            "message": f"Successfully purchased {quantity}x {item.name} for {total_cost} {currency_name}!",
            "item": item,
            "quantity": quantity,
            "cost": total_cost
        }
    
    async def sell_item(self, user_id: int, guild_id: int, item_id: str, quantity: int = 1) -> Dict:
        """Sell item back to shop"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "message": "Item not found"}
        
        # Check if user has enough of the item
        user_items = await self.get_user_items(user_id, guild_id)
        if user_items.get(item_id, 0) < quantity:
            return {
                "success": False, 
                "message": f"You only have {user_items.get(item_id, 0)} of this item"
            }
        
        # Calculate sell price (50% of buy price)
        sell_price = int(item.price * 0.5) * quantity
        
        # Process sale
        await self.remove_user_item(user_id, guild_id, item_id, quantity)
        await self.db.update_user_balance(user_id, guild_id, sell_price, item.currency_type)
        
        currency_name = "coins" if item.currency_type == "balance" else "gems"
        return {
            "success": True,
            "message": f"Sold {quantity}x {item.name} for {sell_price} {currency_name}!",
            "item": item,
            "quantity": quantity,
            "price": sell_price
        }
    
    def format_shop_display(self, category: str = None, page: int = 1, items_per_page: int = 5) -> str:
        """Format shop items for display"""
        items = self.get_shop_items(category)
        
        if not items:
            return "🛒 **Shop is empty**"
        
        # Pagination
        item_list = list(items.values())
        total_pages = (len(item_list) + items_per_page - 1) // items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_items = item_list[start_index:end_index]
        
        shop_text = f"🛒 **SHOP**"
        if category:
            shop_text += f" - {category.title()}"
        shop_text += f" (Page {page}/{total_pages})\n\n"
        
        for item in page_items:
            currency_emoji = "💰" if item.currency_type == "balance" else "💎"
            shop_text += f"**{item.name}** - {item.price} {currency_emoji}\n"
            shop_text += f"*{item.description}*\n"
            if item.max_quantity > 0:
                shop_text += f"*Max: {item.max_quantity}*\n"
            shop_text += f"ID: `{item.item_id}`\n\n"
        
        shop_text += "\n**Use `/buy <item_id> <amount>` to purchase**"
        return shop_text
    
    def format_inventory_display(self, user_items: Dict[str, int], page: int = 1, items_per_page: int = 10) -> str:
        """Format user inventory for display"""
        if not user_items:
            return "🎒 **Your inventory is empty**"
        
        # Filter out items with 0 quantity and sort
        filtered_items = {k: v for k, v in user_items.items() if v > 0}
        
        if not filtered_items:
            return "🎒 **Your inventory is empty**"
        
        # Pagination
        item_list = list(filtered_items.items())
        total_pages = (len(item_list) + items_per_page - 1) // items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_items = item_list[start_index:end_index]
        
        inventory_text = f"🎒 **YOUR INVENTORY** (Page {page}/{total_pages})\n\n"
        
        for item_id, quantity in page_items:
            item = self.get_item(item_id)
            if item:
                inventory_text += f"**{item.name}** x{quantity}\n"
                inventory_text += f"*{item.description}*\n\n"
            else:
                inventory_text += f"**{item_id}** x{quantity}\n*Unknown item*\n\n"
        
        return inventory_text
