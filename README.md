# ListingBuilderPro

Generate optimized product listings for 9 marketplaces in seconds using AI.

![ListingBuilderPro Screenshot](https://listing.automatyzacja-ai.pl)

## Features

- **Multi-Marketplace Support**: Amazon US, DE, UK, FR, IT, ES, eBay, Etsy, Allegro
- **Automatic Translation**: Listings are automatically translated to the appropriate language for each marketplace
- **AI-Powered Generation**: Uses AI to create optimized titles, bullet points, descriptions, and backend keywords
- **Helium 10-Style UI**: Clean, light theme inspired by professional Amazon tools
- **One-Click Copy**: Easily copy any section of your listing

## Supported Marketplaces

| Marketplace | Language | Flag |
|-------------|----------|------|
| Amazon US | English | 🇺🇸 |
| Amazon DE | German | 🇩🇪 |
| Amazon UK | English | 🇬🇧 |
| Amazon FR | French | 🇫🇷 |
| Amazon IT | Italian | 🇮🇹 |
| Amazon ES | Spanish | 🇪🇸 |
| eBay | English | 🛒 |
| Etsy | English | 🎨 |
| Allegro | Polish | 🇵🇱 |

## Live Demo

**URL**: https://listing.automatyzacja-ai.pl

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: n8n workflow automation
- **AI**: LLM-powered listing generation
- **Hosting**: Mikrus VPS + Cloudflare Tunnel

## Generated Listing Includes

- **Title**: Optimized for search (with character count)
- **Bullet Points**: 5 benefit-focused bullets in CAPS format
- **Description**: Detailed product description with benefits
- **Backend Keywords**: SEO-optimized search terms (within byte limits)
- **Tags**: (for Etsy)
- **Item Specifics**: (for eBay)

## Usage

1. Enter your product details:
   - Product name/title
   - Brand
   - Category
   - Description/features
   - Keywords (one per line)

2. Select target marketplaces

3. Click "Generate Listings"

4. Copy generated content for each marketplace

## API

The frontend communicates with an n8n webhook endpoint:

```
POST https://listing.automatyzacja-ai.pl/webhook/v2/product
Headers:
  Content-Type: application/json
  X-API-Key: <your-api-key>
```

## License

MIT

## Author

Created with ❤️ and AI assistance
