import io
import os
import zipfile
from pathlib import Path

from flask import Flask, flash, redirect, render_template_string, request, send_file, url_for
from PIL import Image

app = Flask(__name__)
app.secret_key = os.urandom(24)
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".gif"}
MODELS = ["u2net", "u2netp", "u2net_human_seg"]

HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Background Remover</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
      :root{
        --bg-900: #12111C;
        --bg-800: #16151F;
        --panel: rgba(255,255,255,0.03);
        --accent: #7C5CFA;
        --accent-2: #F0359F;
        --accent-3: #38BDF8;
        --muted: #9CA3AF;
        --text: #F5F5F7;
        --radius: 12px;
      }
      html,body{height:100%;margin:0;background:radial-gradient(600px 400px at 75% 20%, rgba(124,92,250,0.12), transparent), linear-gradient(180deg,var(--bg-900), var(--bg-800));font-family: 'Poppins', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; color:var(--text);}
      .container{max-width:1100px;margin:48px auto;padding:28px;}
      .header{display:flex;align-items:center;justify-content:space-between;gap:20px}
      .brand{display:flex;align-items:center;gap:12px}
      .logo{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--accent), #8B5CF6);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 30px rgba(124,92,250,0.18);}
      .logo svg{width:22px;height:22px;filter:drop-shadow(0 6px 18px rgba(124,92,250,0.18));}
      .title{font-weight:800;font-size:20px;letter-spacing:-0.02em}
      .tagline{color:var(--muted);font-size:13px;margin-top:2px}

      .controls-card{margin-top:18px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:16px;padding:18px;border:1px solid rgba(255,255,255,0.03);box-shadow:0 8px 40px rgba(2,6,23,0.6);display:flex;gap:18px;align-items:center}

      .left{flex:1}
      .right{width:360px}

      .form-row{display:flex;gap:12px;align-items:center}
      label.small{display:block;font-size:11px;color:var(--muted);letter-spacing:1px;margin-bottom:6px}
      select, input[type="text"]{background:transparent;border:1px solid rgba(255,255,255,0.06);padding:10px 12px;border-radius:10px;color:var(--text);width:100px}
      .color-swatch{width:36px;height:36px;border-radius:8px;border:1px solid rgba(255,255,255,0.04);cursor:pointer}

      .upload-zone{margin-top:18px;border:2px dashed rgba(255,255,255,0.06);border-radius:14px;padding:34px;text-align:center;background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent);}
      .upload-zone .folder{width:72px;height:72px;border-radius:14px;background:linear-gradient(180deg, rgba(124,92,250,0.15), rgba(59,130,246,0.04));display:inline-flex;align-items:center;justify-content:center;margin-bottom:14px}
      .upload-zone p{margin:0;font-size:16px}
      .upload-zone a{color:var(--accent);font-weight:600;text-decoration:none}
      .helper{color:var(--muted);font-size:13px;margin-top:8px}

      .actions{display:flex;gap:12px;margin-top:16px;align-items:center}
      .btn{padding:10px 16px;border-radius:10px;border:none;cursor:pointer;font-weight:700}
      .btn.primary{background:linear-gradient(90deg,var(--accent), #8B5CF6);color:white;box-shadow:0 8px 30px rgba(124,92,250,0.18)}
      .btn.secondary{background:transparent;border:1px solid rgba(255,255,255,0.06);color:var(--text)}
      .btn.ghost{background:transparent;border:1px dashed rgba(255,255,255,0.04);color:var(--muted)}
      .btn:disabled{opacity:0.45;cursor:not-allowed}

      .status{color:var(--muted);font-size:13px;margin-left:auto}

      .thumb-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-top:18px}
      .thumb{background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02));border-radius:10px;padding:8px;border:1px solid rgba(255,255,255,0.03);display:flex;flex-direction:column;align-items:center}
      .thumb .canvas{width:120px;height:120px;border-radius:8px;background-image:linear-gradient(45deg,#2b2b2b 25%, transparent 25%), linear-gradient(-45deg,#2b2b2b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2b2b2b 75%), linear-gradient(-45deg, transparent 75%, #2b2b2b 75%);background-size:24px 24px;background-position:0 0,0 12px,12px -12px, -12px 0px;display:flex;align-items:center;justify-content:center;overflow:hidden}
      .thumb img{max-width:100%;max-height:100%;display:block;border-radius:6px}
      .thumb .filename{font-size:12px;color:var(--muted);margin-top:8px;text-align:center}

      /* decorative accents */
      .accent-shape{position:absolute;border-radius:20px;opacity:0.22;pointer-events:none}
      .accent-1{width:220px;height:220px;right:6%;top:6%;background:linear-gradient(135deg,var(--accent),var(--accent-2));filter:blur(20px)}
      .accent-2{width:160px;height:160px;left:4%;top:18%;background:linear-gradient(135deg,var(--accent-3), #6EE7B7);filter:blur(16px)}

      @media(max-width:880px){.right{width:unset}.controls-card{flex-direction:column}.form-row{flex-direction:row;gap:8px}}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <div class="brand">
          <div class="logo" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L13.8 8.6L20.6 9.6L15.3 13.8L16.8 20.4L12 16.9L7.2 20.4L8.7 13.8L3.4 9.6L10.2 8.6L12 2Z" fill="white" opacity="0.95"/></svg>
          </div>
          <div>
            <div class="title">Background Remover</div>
            <div class="tagline">Drop your images below. Backgrounds removed by AI — 100% on your computer, free.</div>
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:12px;color:var(--muted)">Ready to process</div>
        </div>
      </div>

      <div class="controls-card">
        <div class="left">
          <div class="form-row">
            <div style="flex:1">
              <label class="small">MODEL</label>
              <select id="model-select" name="model">
                <option>General (u2net)</option>
                <option>Portraits (u2net_human_seg)</option>
              </select>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <div style="min-width:130px">
                <label class="small">SOLID BACKGROUND</label>
                <div style="display:flex;align-items:center;gap:8px">
                  <input id="solid-toggle" type="checkbox" style="width:18px;height:18px" />
                  <div id="color-swatch" class="color-swatch" title="Pick color" style="background:white"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="upload-zone" id="dropzone">
            <div class="folder">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 7H9L11 9H21V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V7Z" fill="white" opacity="0.9"/></svg>
            </div>
            <p><strong>Drag & drop images here</strong>, or <a href="#" id="browse-link">click to browse</a></p>
            <div class="helper">Supports JPG, PNG, WEBP, BMP, TIFF, GIF — one or hundreds at a time</div>
            <input type="file" id="file-input" multiple accept="image/*" style="display:none" />
          </div>

          <div class="actions">
            <button id="remove-btn" class="btn primary">Remove backgrounds</button>
            <button id="download-btn" class="btn secondary" disabled>Download all (.zip)</button>
            <button id="clear-btn" class="btn ghost">Clear</button>
            <div class="status" id="status-count">0 image(s) ready</div>
          </div>
        </div>

        <div class="right">
          <div style="font-size:13px;color:var(--muted);margin-bottom:10px">Preview</div>
          <div style="height:220px;border-radius:12px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,0.03)">
            <div style="text-align:center;color:var(--muted)">Drop images to see thumbnails below</div>
          </div>
        </div>
      </div>

      <div class="thumb-grid" id="thumb-grid"></div>
    </div>

    <div class="accent-shape accent-1"></div>
    <div class="accent-shape accent-2"></div>

    <script>
      const dropzone = document.getElementById('dropzone');
      const fileInput = document.getElementById('file-input');
      const browseLink = document.getElementById('browse-link');
      const thumbGrid = document.getElementById('thumb-grid');
      const statusCount = document.getElementById('status-count');
      const downloadBtn = document.getElementById('download-btn');
      const clearBtn = document.getElementById('clear-btn');
      const removeBtn = document.getElementById('remove-btn');
      const colorSwatch = document.getElementById('color-swatch');
      const solidToggle = document.getElementById('solid-toggle');

      let files = [];

      function updateStatus(){
        statusCount.textContent = `${files.length} image(s) ready`;
        downloadBtn.disabled = files.length === 0;
      }

      function clearAll(){ files=[]; thumbGrid.innerHTML=''; updateStatus(); }

      function addFiles(list){
        Array.from(list).forEach(f => {
          files.push(f);
          const node = document.createElement('div'); node.className='thumb';
          const canvas = document.createElement('div'); canvas.className='canvas';
          const img = document.createElement('img');
          const reader = new FileReader();
          reader.onload = e => { img.src = e.target.result; };
          reader.readAsDataURL(f);
          canvas.appendChild(img);
          const name = document.createElement('div'); name.className='filename'; name.textContent = f.name;
          node.appendChild(canvas); node.appendChild(name);
          thumbGrid.appendChild(node);
        });
        updateStatus();
      }

      dropzone.addEventListener('click', () => fileInput.click());
      browseLink.addEventListener('click', (e)=>{ e.preventDefault(); fileInput.click(); });
      fileInput.addEventListener('change', (e)=> addFiles(e.target.files));

      dropzone.addEventListener('dragover', e=>{ e.preventDefault(); dropzone.style.borderColor='rgba(124,92,250,0.6)'; });
      dropzone.addEventListener('dragleave', e=>{ dropzone.style.borderColor='rgba(255,255,255,0.06)'; });
      dropzone.addEventListener('drop', e=>{ e.preventDefault(); dropzone.style.borderColor='rgba(255,255,255,0.06)'; addFiles(e.dataTransfer.files); });

      clearBtn.addEventListener('click', ()=> clearAll());

      // simple color picker
      colorSwatch.addEventListener('click', ()=>{
        const inp = document.createElement('input'); inp.type='color'; inp.value='#ffffff'; inp.style.position='fixed'; inp.style.left='-9999px'; document.body.appendChild(inp);
        inp.click(); inp.addEventListener('input', ()=>{ colorSwatch.style.background = inp.value; document.body.removeChild(inp); });
      });

      removeBtn.addEventListener('click', ()=>{
        if(files.length===0) return alert('No images selected');
        removeBtn.disabled=true; removeBtn.textContent='Processing...';
        // submit to server via fetch with FormData
        const fd = new FormData();
        files.forEach(f=> fd.append('images', f));
        fd.append('model', document.getElementById('model-select').value);
        if(solidToggle.checked) fd.append('bg_color', colorSwatch.style.background || '255,255,255');
        fetch('/', {method:'POST', body:fd}).then(r=> r.blob()).then(blob=>{
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a'); a.href=url; a.download='backgrounds-removed.zip'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
          removeBtn.disabled=false; removeBtn.textContent='Remove backgrounds';
        }).catch(err=>{ alert('Processing failed'); removeBtn.disabled=false; removeBtn.textContent='Remove backgrounds'; });
      });
    </script>
  </body>
</html>
"""


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXT


def process_bytes(data: bytes, model_name: str, bg_color: str) -> bytes:
    from rembg import remove

    try:
        result = remove(data, model_name=model_name)
    except TypeError:
        result = remove(data, model=model_name)
    image = Image.open(io.BytesIO(result)).convert("RGBA")
    if bg_color:
        rgb = tuple(int(part) for part in bg_color.split(","))
        background = Image.new("RGBA", image.size, (*rgb, 255))
        image = Image.alpha_composite(background, image)
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.getvalue()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("images")
        if not files or not any(f.filename for f in files):
            flash("Please choose at least one image.")
            return redirect(url_for("index"))

        bg_color = request.form.get("bg_color", "").strip()
        model = request.form.get("model", "u2net")
        outputs = []
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            for upload in files:
                if not upload or not upload.filename:
                    continue
                if not allowed_file(upload.filename):
                    continue
                data = upload.read()
                result = process_bytes(data, model, bg_color)
                filename = f"{Path(upload.filename).stem}.png"
                zip_out.writestr(filename, result)
                outputs.append(filename)

        if not outputs:
            flash("No supported image files were uploaded.")
            return redirect(url_for("index"))

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="backgrounds-removed.zip",
        )

    return render_template_string(HTML, models=MODELS, default_model="u2net")


if __name__ == "__main__":
    app.run(debug=True)
