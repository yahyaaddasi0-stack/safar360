add_shortcode('awraq_sard_main_page', function () {
    $category_specs = array(
        array('name' => 'التاريخ والوقائع', 'slug' => 'history', 'id' => 44),
        array('name' => 'الآثار والاكتشافات', 'slug' => 'athar', 'id' => 47),
        array('name' => 'الأدب والفنون', 'slug' => 'artsl', 'id' => 48),
        array('name' => 'الشعوب والأنثروبولوجيا', 'slug' => 'anthropology', 'id' => 45),
        array('name' => 'الفلسفة والفكر', 'slug' => 'philosophy', 'id' => 46),
        array('name' => 'الموسيقى والأنغام', 'slug' => 'musicology', 'id' => 49),
        array('name' => 'آفاق', 'slug' => 'afaq', 'id' => 50),
    );

    $category_ids = array_map(function ($item) { return (int) $item['id']; }, $category_specs);
    $category_ids[] = 66; // Collection: سرد8; retained as a series, not a primary subject category.
    $query = new WP_Query(array(
        'post_type' => 'post',
        'post_status' => 'publish',
        'posts_per_page' => 100,
        'category__in' => $category_ids,
        'orderby' => 'date',
        'order' => 'DESC',
        'ignore_sticky_posts' => true,
        'no_found_rows' => true,
    ));

    $posts = array();
    $category_images = array();
    foreach ($query->posts as $post_item) {
        $assigned_ids = wp_get_post_categories($post_item->ID);
        $primary = null;
        foreach ($category_specs as $spec) {
            if (in_array((int) $spec['id'], array_map('intval', $assigned_ids), true)) {
                $primary = $spec;
                break;
            }
        }
        if (!$primary && in_array(66, array_map('intval', $assigned_ids), true)) {
            $primary = array('name' => 'سرد8', 'slug' => 'sard8article', 'id' => 66);
        }
        if (!$primary) {
            continue;
        }

        $image = get_the_post_thumbnail_url($post_item->ID, 'large');
        if (!$image) {
            $content = get_post_field('post_content', $post_item->ID);
            if (preg_match('/<img[^>]+src=["\']([^"\']+)/i', $content, $match)) {
                $image = esc_url_raw($match[1]);
            }
        }
        $excerpt = get_the_excerpt($post_item);
        if (!$excerpt) {
            $excerpt = wp_trim_words(wp_strip_all_tags(strip_shortcodes($post_item->post_content)), 27, '…');
        }
        $entry = array(
            'id' => (int) $post_item->ID,
            'title' => get_the_title($post_item),
            'url' => get_permalink($post_item),
            'excerpt' => wp_strip_all_tags($excerpt),
            'image' => $image ? esc_url_raw($image) : '',
            'category' => $primary['name'],
            'category_slug' => $primary['slug'],
            'date' => get_the_date('j F Y', $post_item),
            'timestamp' => (int) get_post_timestamp($post_item),
        );
        $posts[] = $entry;
        if ($image && isset($category_images[$primary['slug']]) === false) {
            $category_images[$primary['slug']] = esc_url_raw($image);
        }
    }
    wp_reset_postdata();

    foreach ($category_specs as &$spec) {
        $term = get_category($spec['id']);
        $spec['count'] = $term ? (int) $term->count : 0;
        $spec['url'] = get_category_link($spec['id']);
        $spec['image'] = isset($category_images[$spec['slug']]) ? $category_images[$spec['slug']] : '';
    }
    unset($spec);
    $series = array(
        'name' => 'سرد8',
        'slug' => 'sard8article',
        'count' => (int) (get_category(66) ? get_category(66)->count : 0),
        'url' => get_category_link(66),
        'image' => isset($category_images['sard8article']) ? $category_images['sard8article'] : '',
    );
    $payload = array('posts' => $posts, 'categories' => $category_specs, 'series' => $series);
    $json_flags = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT;
    $payload_json = wp_json_encode($payload, $json_flags);
    if (!$payload_json) {
        $payload_json = '{"posts":[],"categories":[],"series":{}}';
    }
    $total = count($posts);
    $hero_image = !empty($posts[0]['image']) ? $posts[0]['image'] : '';
    ob_start();
    ?>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
      #awraq-sard-library, #awraq-sard-library * { box-sizing:border-box; }
      #awraq-sard-library {
        --as-bg:#101715; --as-panel:#171f1c; --as-panel-2:#1c2622; --as-gold:#d5b06a;
        --as-gold-soft:rgba(213,176,106,.16); --as-cream:#f2eee4; --as-muted:#b9c2bc;
        --as-line:rgba(239,231,211,.12); --as-radius:20px;
        position:relative; left:50%; width:100vw; max-width:100vw; transform:translateX(-50%);
        overflow:hidden; direction:rtl; color:var(--as-cream); background:
          radial-gradient(ellipse at 12% 7%, rgba(99,123,94,.20), transparent 30rem),
          radial-gradient(ellipse at 92% 31%, rgba(176,132,63,.10), transparent 34rem),
          linear-gradient(180deg,#101715 0%,#121a17 50%,#101715 100%);
        font-family:'Cairo',Tahoma,Arial,sans-serif; line-height:1.8; padding:0 0 68px;
        isolation:isolate;
      }
      #awraq-sard-library:before { content:""; position:absolute; inset:0; z-index:-1; opacity:.16; pointer-events:none;
        background-image:radial-gradient(rgba(255,255,255,.22) .55px,transparent .7px); background-size:7px 7px; mask-image:linear-gradient(180deg,#000,transparent 68%); }
      #awraq-sard-library a { color:inherit; text-decoration:none; }
      #awraq-sard-library .as-wrap { width:min(1280px,calc(100% - 40px)); margin-inline:auto; }
      #awraq-sard-library .as-hero { min-height:400px; position:relative; display:grid; grid-template-columns:minmax(0,1.25fr) minmax(270px,.75fr); gap:38px; align-items:center; padding:74px 0 54px; }
      #awraq-sard-library .as-hero:after { content:""; position:absolute; width:390px; height:390px; border:1px solid rgba(213,176,106,.12); border-radius:50%; top:-220px; left:42%; box-shadow:0 0 0 28px rgba(213,176,106,.025),0 0 0 62px rgba(213,176,106,.018); pointer-events:none; }
      #awraq-sard-library .as-kicker { color:var(--as-gold); display:flex; align-items:center; gap:11px; font-size:12px; font-weight:700; letter-spacing:.08em; margin:0 0 12px; }
      #awraq-sard-library .as-kicker:before { content:""; width:34px; height:1px; background:var(--as-gold); }
      #awraq-sard-library .as-hero h1 { color:var(--as-cream); font-size:clamp(42px,6vw,76px); line-height:1.15; font-weight:700; letter-spacing:-.035em; margin:0 0 20px; }
      #awraq-sard-library .as-hero h1 em { color:var(--as-gold); font-style:normal; }
      #awraq-sard-library .as-lead { max-width:690px; color:#d0d4cc; font-size:clamp(15px,1.5vw,18px); line-height:2; margin:0; }
      #awraq-sard-library .as-actions { display:flex; align-items:center; flex-wrap:wrap; gap:12px; margin-top:27px; }
      #awraq-sard-library .as-button { min-height:46px; display:inline-flex; align-items:center; justify-content:center; gap:9px; border-radius:999px; padding:10px 20px; font-weight:700; font-size:13px; transition:transform .25s ease,background .25s ease,border-color .25s ease; }
      #awraq-sard-library .as-button:hover { transform:translateY(-2px); }
      #awraq-sard-library .as-button-primary { background:linear-gradient(135deg,#e0c17d,#b38b47); color:#17201b; box-shadow:0 8px 24px rgba(175,133,66,.18); }
      #awraq-sard-library .as-button-ghost { border:1px solid var(--as-line); color:var(--as-cream); background:rgba(255,255,255,.025); }
      #awraq-sard-library .as-hero-art { position:relative; min-height:270px; border-radius:var(--as-radius); overflow:hidden; border:1px solid rgba(213,176,106,.24); background:linear-gradient(145deg,#29382f,#101715); box-shadow:0 28px 65px rgba(0,0,0,.28); }
      #awraq-sard-library .as-hero-art:before { content:""; position:absolute; inset:0; background:linear-gradient(90deg,rgba(16,23,21,.1),rgba(16,23,21,.2) 36%,rgba(16,23,21,.88)),linear-gradient(0deg,rgba(16,23,21,.48),transparent 58%); z-index:1; }
      #awraq-sard-library .as-hero-art img { width:100%; height:100%; min-height:270px; position:absolute; inset:0; object-fit:cover; opacity:.77; transition:transform .8s ease; }
      #awraq-sard-library .as-hero-art:hover img { transform:scale(1.04); }
      #awraq-sard-library .as-art-caption { position:absolute; z-index:2; bottom:22px; right:24px; left:24px; display:flex; justify-content:space-between; align-items:end; gap:14px; }
      #awraq-sard-library .as-art-caption strong { display:block; font-size:17px; max-width:300px; line-height:1.7; }
      #awraq-sard-library .as-art-caption span { color:var(--as-gold); font-size:11px; white-space:nowrap; }
      #awraq-sard-library .as-stats { display:flex; flex-wrap:wrap; gap:10px; margin-top:29px; }
      #awraq-sard-library .as-stat { display:flex; align-items:center; gap:9px; border-inline-start:1px solid var(--as-line); padding:2px 0 2px 18px; }
      #awraq-sard-library .as-stat b { color:var(--as-gold); font-size:20px; font-weight:700; }
      #awraq-sard-library .as-stat span { color:var(--as-muted); font-size:11px; }
      #awraq-sard-library .as-section { margin-top:50px; }
      #awraq-sard-library .as-section-head { display:flex; justify-content:space-between; align-items:end; gap:18px; margin-bottom:20px; }
      #awraq-sard-library .as-section-head h2 { color:var(--as-cream); font-size:clamp(23px,3vw,32px); line-height:1.35; margin:0; font-weight:700; }
      #awraq-sard-library .as-section-head p { margin:5px 0 0; color:var(--as-muted); font-size:12px; }
      #awraq-sard-library .as-eyebrow { color:var(--as-gold); font-size:10px; font-weight:700; letter-spacing:.08em; display:block; margin-bottom:5px; }
      #awraq-sard-library .as-category-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
      #awraq-sard-library .as-category { position:relative; min-height:150px; overflow:hidden; border-radius:16px; border:1px solid var(--as-line); background:linear-gradient(145deg,#26342c,#17201d); isolation:isolate; transition:transform .25s ease,border-color .25s ease; }
      #awraq-sard-library .as-category:hover { transform:translateY(-3px); border-color:rgba(213,176,106,.48); }
      #awraq-sard-library .as-category img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:.48; z-index:-2; transition:transform .6s ease,opacity .3s ease; }
      #awraq-sard-library .as-category:hover img { transform:scale(1.06); opacity:.62; }
      #awraq-sard-library .as-category:after { content:""; position:absolute; inset:0; z-index:-1; background:linear-gradient(0deg,rgba(13,20,17,.97),rgba(13,20,17,.22)); }
      #awraq-sard-library .as-category-copy { position:absolute; inset:auto 17px 15px; display:flex; justify-content:space-between; align-items:end; gap:8px; }
      #awraq-sard-library .as-category-copy strong { font-size:15px; line-height:1.55; }
      #awraq-sard-library .as-category-copy small { color:var(--as-gold); white-space:nowrap; font-size:10px; }
      #awraq-sard-library .as-featured { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }
      #awraq-sard-library .as-feature { min-width:0; display:grid; grid-template-columns:104px minmax(0,1fr); gap:14px; align-items:center; border:1px solid var(--as-line); border-radius:17px; padding:11px; background:linear-gradient(135deg,rgba(255,255,255,.045),rgba(255,255,255,.012)); transition:transform .28s ease,border-color .28s ease; animation:as-rise .55s both; }
      #awraq-sard-library .as-feature:hover { transform:translateY(-3px); border-color:rgba(213,176,106,.4); }
      #awraq-sard-library .as-feature img { width:104px; height:82px; object-fit:cover; border-radius:11px; background:#26342c; }
      #awraq-sard-library .as-feature-label { color:var(--as-gold); display:block; font-size:9px; margin-bottom:3px; }
      #awraq-sard-library .as-feature strong { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; color:var(--as-cream); font-size:12px; line-height:1.65; }
      #awraq-sard-library .as-refresh { cursor:pointer; border:1px solid rgba(213,176,106,.3); background:transparent; color:var(--as-gold); font:inherit; font-size:11px; border-radius:999px; padding:8px 13px; transition:background .2s ease,transform .2s ease; white-space:nowrap; }
      #awraq-sard-library .as-refresh:hover { background:var(--as-gold-soft); transform:rotate(-2deg); }
      #awraq-sard-library .as-library { scroll-margin-top:20px; }
      #awraq-sard-library .as-toolbar { display:flex; align-items:center; gap:12px; justify-content:space-between; flex-wrap:wrap; margin:19px 0 20px; }
      #awraq-sard-library .as-filters { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
      #awraq-sard-library .as-filter { cursor:pointer; color:#d6dbd5; background:rgba(255,255,255,.025); border:1px solid var(--as-line); border-radius:999px; padding:8px 13px; font-family:inherit; font-size:11px; transition:all .2s ease; }
      #awraq-sard-library .as-filter:hover,#awraq-sard-library .as-filter[aria-pressed="true"] { color:#18201b; border-color:var(--as-gold); background:linear-gradient(135deg,#e0c17d,#b38b47); }
      #awraq-sard-library .as-search { display:flex; align-items:center; gap:8px; width:min(280px,100%); min-height:42px; padding:0 13px; border:1px solid var(--as-line); border-radius:999px; background:rgba(255,255,255,.035); color:var(--as-cream); }
      #awraq-sard-library .as-search input { width:100%; border:0; outline:0; background:transparent; color:var(--as-cream); font:inherit; font-size:12px; }
      #awraq-sard-library .as-search input::placeholder { color:#929d95; }
      #awraq-sard-library .as-result-line { color:var(--as-muted); font-size:11px; min-height:22px; margin:0 0 12px; }
      #awraq-sard-library .as-article-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:17px; }
      #awraq-sard-library .as-card { min-width:0; min-height:350px; display:flex; flex-direction:column; border-radius:17px; overflow:hidden; border:1px solid var(--as-line); background:linear-gradient(155deg,#1b2420,#151c19); transition:transform .28s ease,border-color .28s ease,box-shadow .28s ease; animation:as-rise .48s both; }
      #awraq-sard-library .as-card:hover { transform:translateY(-4px); border-color:rgba(213,176,106,.42); box-shadow:0 17px 40px rgba(0,0,0,.22); }
      #awraq-sard-library .as-card-media { position:relative; aspect-ratio:16 / 10; overflow:hidden; background:linear-gradient(135deg,#26342c,#18201c); }
      #awraq-sard-library .as-card-media img { width:100%; height:100%; object-fit:cover; display:block; transition:transform .7s ease; }
      #awraq-sard-library .as-card:hover .as-card-media img { transform:scale(1.045); }
      #awraq-sard-library .as-card-tag { position:absolute; right:12px; top:12px; max-width:calc(100% - 24px); padding:4px 9px; border:1px solid rgba(213,176,106,.25); border-radius:99px; background:rgba(12,18,15,.76); color:#e3c783; backdrop-filter:blur(8px); font-size:9px; }
      #awraq-sard-library .as-card-body { display:flex; flex:1; flex-direction:column; align-items:flex-start; padding:15px 16px 16px; }
      #awraq-sard-library .as-card-date { color:#99a49c; font-size:9px; margin-bottom:5px; }
      #awraq-sard-library .as-card h3 { color:var(--as-cream); font-size:14px; line-height:1.8; margin:0 0 8px; font-weight:700; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
      #awraq-sard-library .as-card p { color:#b9c2bc; font-size:11px; line-height:1.9; margin:0 0 16px; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
      #awraq-sard-library .as-read { color:var(--as-gold); font-size:11px; font-weight:700; margin-top:auto; display:inline-flex; gap:7px; align-items:center; }
      #awraq-sard-library .as-read:after { content:"←"; transition:transform .2s ease; }
      #awraq-sard-library .as-card:hover .as-read:after { transform:translateX(-4px); }
      #awraq-sard-library .as-empty { display:none; text-align:center; border:1px dashed var(--as-line); border-radius:16px; color:var(--as-muted); padding:32px; }
      #awraq-sard-library .as-more-wrap { text-align:center; margin:28px 0 0; }
      #awraq-sard-library .as-more { cursor:pointer; border:1px solid rgba(213,176,106,.38); background:rgba(213,176,106,.08); color:var(--as-gold); font:inherit; font-size:12px; border-radius:999px; padding:11px 22px; transition:all .2s ease; }
      #awraq-sard-library .as-more:hover { color:#18201b; background:var(--as-gold); }
      @keyframes as-rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
      @media (max-width:1100px) { #awraq-sard-library .as-article-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } #awraq-sard-library .as-category-grid { grid-template-columns:repeat(4,minmax(0,1fr)); } }
      @media (max-width:820px) { #awraq-sard-library .as-hero { grid-template-columns:1fr; min-height:0; gap:24px; padding:50px 0 38px; } #awraq-sard-library .as-hero-art { min-height:225px; } #awraq-sard-library .as-hero-art img { min-height:225px; } #awraq-sard-library .as-featured { grid-template-columns:1fr; } #awraq-sard-library .as-category-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } #awraq-sard-library .as-article-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
      @media (max-width:560px) { #awraq-sard-library .as-wrap { width:min(100% - 28px,1280px); } #awraq-sard-library .as-hero { padding-top:39px; } #awraq-sard-library .as-hero h1 { font-size:44px; } #awraq-sard-library .as-section { margin-top:36px; } #awraq-sard-library .as-section-head { align-items:start; } #awraq-sard-library .as-category-grid { gap:9px; } #awraq-sard-library .as-category { min-height:120px; border-radius:14px; } #awraq-sard-library .as-category-copy { inset:auto 11px 11px; display:block; } #awraq-sard-library .as-category-copy strong { display:block; font-size:12px; } #awraq-sard-library .as-category-copy small { display:block; margin-top:3px; } #awraq-sard-library .as-toolbar { align-items:stretch; } #awraq-sard-library .as-filters { flex-wrap:nowrap; overflow-x:auto; padding:3px 0 8px; scrollbar-width:thin; } #awraq-sard-library .as-filter { flex:0 0 auto; } #awraq-sard-library .as-search { width:100%; } #awraq-sard-library .as-article-grid { grid-template-columns:1fr; gap:12px; } #awraq-sard-library .as-card { min-height:0; display:grid; grid-template-columns:122px minmax(0,1fr); } #awraq-sard-library .as-card-media { aspect-ratio:auto; min-height:155px; height:100%; } #awraq-sard-library .as-card-body { padding:11px 12px; } #awraq-sard-library .as-card h3 { font-size:12px; -webkit-line-clamp:3; margin-bottom:4px; } #awraq-sard-library .as-card p { font-size:10px; -webkit-line-clamp:2; margin-bottom:8px; } #awraq-sard-library .as-card-tag { top:8px; right:8px; font-size:8px; padding:3px 7px; } #awraq-sard-library .as-read { font-size:10px; } #awraq-sard-library .as-feature { grid-template-columns:94px minmax(0,1fr); } #awraq-sard-library .as-feature img { width:94px; height:76px; } }
      @media (max-width:365px) { #awraq-sard-library .as-card { grid-template-columns:104px minmax(0,1fr); } #awraq-sard-library .as-category-copy strong { font-size:11px; } }
      @media (prefers-reduced-motion:reduce) { #awraq-sard-library *,#awraq-sard-library *:before,#awraq-sard-library *:after { scroll-behavior:auto!important; animation-duration:.01ms!important; animation-iteration-count:1!important; transition-duration:.01ms!important; } }
    </style>
    <section id="awraq-sard-library" aria-labelledby="as-main-title">
      <div class="as-wrap">
        <header class="as-hero">
          <div class="as-hero-copy">
            <p class="as-kicker">قراءات وتحقيقات من سرد 360</p>
            <h1 id="as-main-title">أوراق <em>سرد</em></h1>
            <p class="as-lead">مساحة للبحث الهادئ في طبقات التاريخ والإنسان والفكرة؛ مقالات تُقرأ بتمهّل، وتفتح نافذة جديدة على الحكايات التي تستحق أن تُروى.</p>
            <div class="as-actions">
              <a class="as-button as-button-primary" href="#as-library">ابدأ القراءة <span aria-hidden="true">←</span></a>
              <a class="as-button as-button-ghost" href="https://sard360.com/">العودة إلى سرد 360</a>
            </div>
            <div class="as-stats" aria-label="إحصاءات المكتبة">
              <div class="as-stat"><b><?php echo esc_html($total); ?></b><span>مقالاً وبحثاً</span></div>
              <div class="as-stat"><b><?php echo esc_html(count($category_specs)); ?></b><span>مسارات معرفية</span></div>
              <div class="as-stat"><b>360°</b><span>زاوية أخرى للحكاية</span></div>
            </div>
          </div>
          <a class="as-hero-art" href="<?php echo !empty($posts[0]['url']) ? esc_url($posts[0]['url']) : '#as-library'; ?>" aria-label="اقرأ أحدث أوراق سرد">
            <?php if ($hero_image) : ?><img src="<?php echo esc_url($hero_image); ?>" alt="" fetchpriority="high" decoding="async"><?php endif; ?>
            <span class="as-art-caption"><strong><?php echo !empty($posts[0]['title']) ? esc_html($posts[0]['title']) : 'حكاية جديدة تنتظر القراءة'; ?></strong><span>من أحدث أوراق سرد</span></span>
          </a>
        </header>

        <section class="as-section" aria-labelledby="as-categories-title">
          <div class="as-section-head"><div><span class="as-eyebrow">مسارات القراءة</span><h2 id="as-categories-title">اختر الباب الذي يثير فضولك</h2><p>تصفّح الموضوعات أو انتقل مباشرة إلى أوراقها.</p></div></div>
          <div class="as-category-grid">
            <?php foreach ($category_specs as $spec) : ?>
              <a class="as-category" href="<?php echo esc_url($spec['url']); ?>" data-awraq-filter="<?php echo esc_attr($spec['slug']); ?>">
                <?php if ($spec['image']) : ?><img src="<?php echo esc_url($spec['image']); ?>" alt="" loading="lazy" decoding="async"><?php endif; ?>
                <span class="as-category-copy"><strong><?php echo esc_html($spec['name']); ?></strong><small><?php echo esc_html($spec['count']); ?> مقالاً</small></span>
              </a>
            <?php endforeach; ?>
          </div>
        </section>

        <section class="as-section" aria-labelledby="as-picks-title">
          <div class="as-section-head"><div><span class="as-eyebrow">اقرأ بعدها</span><h2 id="as-picks-title">ترشيحات سرد</h2><p>ثلاث أوراق تفتح مسارات متنوّعة في أرشيف سرد.</p></div><button class="as-refresh" type="button" data-as-refresh>ترشيحات أخرى <span aria-hidden="true">↻</span></button></div>
          <div class="as-featured" data-as-featured></div>
        </section>

        <section class="as-section as-library" id="as-library" aria-labelledby="as-library-title">
          <div class="as-section-head"><div><span class="as-eyebrow">المكتبة الكاملة</span><h2 id="as-library-title">كل أوراق سرد</h2><p>ابحث في المقالات، أو صفِّها بحسب موضوعها.</p></div></div>
          <div class="as-toolbar">
            <nav class="as-filters" aria-label="تصفية أوراق سرد">
              <button type="button" class="as-filter" data-as-filter="all" aria-pressed="true">كل الأوراق</button>
              <?php foreach ($category_specs as $spec) : ?><button type="button" class="as-filter" data-as-filter="<?php echo esc_attr($spec['slug']); ?>" aria-pressed="false"><?php echo esc_html($spec['name']); ?></button><?php endforeach; ?>
              <button type="button" class="as-filter" data-as-filter="sard8article" aria-pressed="false">سرد8</button>
            </nav>
            <label class="as-search"><span aria-hidden="true">⌕</span><input type="search" placeholder="ابحث بعنوان أو فكرة…" aria-label="ابحث في مقالات أوراق سرد" data-as-search></label>
          </div>
          <p class="as-result-line" data-as-status aria-live="polite"></p>
          <div class="as-article-grid" data-as-grid></div>
          <p class="as-empty" data-as-empty>لم نعثر على ورقة تطابق بحثك. جرّب كلمة أخرى أو اختر كل الأوراق.</p>
          <div class="as-more-wrap"><button type="button" class="as-more" data-as-more>عرض مزيد من الأوراق</button></div>
        </section>
      </div>
    </section>
    <script>
    (()=>{
      const DATA=<?php echo $payload_json; ?>;
      const root=document.getElementById('awraq-sard-library');
      if(!root||!DATA||!Array.isArray(DATA.posts))return;
      const posts=DATA.posts, grid=root.querySelector('[data-as-grid]'), featured=root.querySelector('[data-as-featured]');
      const search=root.querySelector('[data-as-search]'), status=root.querySelector('[data-as-status]'), empty=root.querySelector('[data-as-empty]'), more=root.querySelector('[data-as-more]');
      let active='all', query='', shown=12, pool=[]; const pageSize=12;
      const escapeHtml=value=>String(value||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      const shuffle=list=>{const a=list.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
      const filtered=()=>posts.filter(p=>(active==='all'||p.category_slug===active)&&(!query||(p.title+' '+p.excerpt+' '+p.category).toLocaleLowerCase().includes(query)));
      function renderFeatured(){
        if(!pool.length)pool=shuffle(posts); const picks=pool.slice(0,Math.min(3,pool.length));
        if(!picks.length){featured.innerHTML='<p class="as-empty">تعود الترشيحات قريباً.</p>';return;}
        featured.innerHTML=picks.map((p,i)=>`<a class="as-feature" href="${escapeHtml(p.url)}" style="animation-delay:${i*70}ms"><img src="${escapeHtml(p.image)}" alt="" loading="lazy"><span><small class="as-feature-label">${escapeHtml(p.category)} · ترشيح سرد</small><strong>${escapeHtml(p.title)}</strong></span></a>`).join('');
        pool=pool.slice(picks.length); if(pool.length<3)pool=shuffle(posts.filter(p=>!picks.some(x=>x.id===p.id)));
      }
      function render(){
        const list=filtered(), visible=list.slice(0,shown);
        status.textContent=`تُعرض ${visible.length} من ${list.length} ورقة`;
        empty.style.display=list.length?'none':'block'; grid.style.display=list.length?'grid':'none';
        more.style.display=list.length>shown?'inline-flex':'none';
        grid.innerHTML=visible.map((p,i)=>`<article class="as-card" style="animation-delay:${Math.min(i,8)*35}ms"><a class="as-card-media" href="${escapeHtml(p.url)}" aria-label="اقرأ: ${escapeHtml(p.title)}">${p.image?`<img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.title)}" loading="lazy" decoding="async">`:''}<span class="as-card-tag">${escapeHtml(p.category)}</span></a><div class="as-card-body"><time class="as-card-date">${escapeHtml(p.date)}</time><h3><a href="${escapeHtml(p.url)}">${escapeHtml(p.title)}</a></h3><p>${escapeHtml(p.excerpt)}</p><a class="as-read" href="${escapeHtml(p.url)}">اقرأ الورقة</a></div></article>`).join('');
      }
      root.querySelectorAll('[data-as-filter]').forEach(button=>button.addEventListener('click',()=>{active=button.dataset.asFilter;shown=pageSize;root.querySelectorAll('[data-as-filter]').forEach(x=>x.setAttribute('aria-pressed',x===button?'true':'false'));render();}));
      root.querySelectorAll('[data-awraq-filter]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();const slug=link.dataset.awraqFilter;const button=root.querySelector(`[data-as-filter="${CSS.escape(slug)}"]`);if(button){button.click();root.querySelector('#as-library').scrollIntoView({behavior:'smooth',block:'start'});}}));
      search.addEventListener('input',()=>{query=search.value.trim().toLocaleLowerCase();shown=pageSize;render();});
      more.addEventListener('click',()=>{shown+=pageSize;render();});
      root.querySelector('[data-as-refresh]').addEventListener('click',()=>{pool=shuffle(posts);renderFeatured();});
      renderFeatured();render();
    })();
    </script>
    <?php
    return ob_get_clean();
});
