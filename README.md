# AI Generator API

## Description

**Flask AI Generator API** is a Flask-based API that allows generating images, music, and tags from textual descriptions or input images. It provides multiple endpoints to facilitate on-demand multimedia content creation. <br />
It based on:
- Stable diffusion for images
- MusicGen for music
- Google-T5 for tags

---

## Features

- **Generate images from a text prompt**
- **Generate images from another image (buffer)**
- **Generate 30-second music from a textual description**
- **Generate tags for multimedia content based on the image and sound**

---

## Installation

### Prerequisites
- Docker

### Run & build the project
Run `docker-compose up -d`

### Rebuild
Run `docker-compose build --no-cache`

### Unmount the Container
Associated images and builds will not be affected <br />
Run `docker-compose down`

---

## Usage

### 1. Generate an Image from a Text Prompt

**Endpoint:** `POST /generate/image/prompt`

**Request Body:**
```json
{
    "prompt": "a cat riding a bicycle in the rain"
}
```

**Response:**
```json
{
    "generation_id": "an_uuid",
    "file_path": "https://yourserver.com/output/generated_image/image123.png"
}
```

---

### 2. Generate an Image from Another Image

**Endpoint:** `POST /generate/image/image`

**Request Body:**
- Image sent as a buffer (multipart/form-data)

**Response:**
```json
{
    "generation_id": "an_uuid",
    "file_path": "https://yourserver.com/output/generated_image/image123.png"
}
```

---

### 3. Generate Music from a Description

**Endpoint:** `POST /generate/sound`

**Request Body:**
```json
{
    "description": "a calm and relaxing seaside ambiance"
}
```

**Response:**
```json
{
    "generation_id": "an_uuid",
    "file_path": "https://yourserver.com/output/generated_sound/sound123.wav"
}
```

---

### 4. Generate Tags from Image and Sound

**Endpoint:** `POST /generate/tags`

**Request Body:**
```json
{
    "image_prompt": "a cat riding a bicycle in the rain",
    "sound_description": "a calm and relaxing seaside ambiance"
}
```

**Response:**
```json
{
    "tags": ["cat", "bicycle", "rain", "calm", "relaxing", "sea"]
}
```

---

## Contribution

Contributions are welcome! To contribute:
1. Fork the project
2. Create a branch (`feature/new-feature`)
3. Make your modifications and add commits
4. Push your branch
5. Submit a Pull Request

