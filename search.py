import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic, RateLimitError
from google import genai

load_dotenv()

class LLMManager:
    def __init__(self):
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = Anthropic(api_key=self.claude_key) if self.claude_key else None
        
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=self.gemini_key) if self.gemini_key else None

    def generate_search_url(self, user_query: str) -> str:
        """
        Takes a natural English query and generates the appropriate 99acres search URL.
        """
        prompt = f"""
        You are a url generation tool for 99acres. Analyzed the user's real estate search query and return a valid search URL.
        
        User Query: "{user_query}"
        
        Rules for 99acres formatting:
        1. General format for rental properties: https://www.99acres.com/property-for-rent-in-[city_name]-ffid
        2. Clean the city name (lowercase, use hyphens for spaces). E.g., "Erode" becomes "erode", "New Delhi" becomes "new-delhi".
        3. If no specific city is found, default to "erode".
        
        Return ONLY a raw JSON object with a single key "url". Do not include any markdown fences or explanation text.
        Example output format:
        {{"url": "https://www.99acres.com/property-for-rent-in-erode-ffid"}}
        """
        
        # Try Claude first
        if self.claude_client:
            try:
                response = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=150,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                data = json.loads(response.content[0].text.strip())
                return data.get("url")
            except RateLimitError:
                pass # Failover to Gemini below
            except Exception as e:
                print(f"⚠️ Claude URL generation failed: {e}. Trying Gemini...")

        # Gemini Backup
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                # Clean up string if markdown JSON wrapping happened
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                return data.get("url")
            except Exception as e:
                print(f"❌ Gemini URL generation failed: {e}")
                
        # Default fallback if both fail
        return "https://www.99acres.com/property-for-rent-in-erode-ffid"

    def analyze_listings(self, user_query, scraped_data):
        prompt = f"""
        You are an expert real estate assistant. Deeply analyze the following raw scraped property data against the user's criteria.
        
        User Criteria: "{user_query}"
        
        Raw Data:
        {scraped_data}
        
        Provide a structured, ranked list of matching properties. For each, include:
        1. Title & Location
        2. Price & Configuration (e.g., 2BHK)
        3. Match Score (0-100%) and a brief justification highlighting if it matches specific things like gated community, parking, or budget limits mentioned by the user.
        """

        if self.claude_client:
            try:
                print("🤖 Querying Claude (Primary Analysis)...")
                response = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=2000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except RateLimitError:
                print("⚠️ Claude API limit reached or rate-limited. Falling back to Gemini...")
            except Exception as e:
                print(f"⚠️ Claude encountered an error: {e}. Trying Gemini...")
        
        if self.gemini_client:
            try:
                print("♊ Querying Gemini (Backup Analysis)...")
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                return f"❌ Both APIs failed. Gemini Error: {e}"
        
        return "❌ No API keys configured or both providers are unavailable."