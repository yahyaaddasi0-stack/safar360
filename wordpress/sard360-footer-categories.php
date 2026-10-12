add_action('wp_footer', function () {
    if (is_admin()) {
        return;
    }
    $navigation = array(
        'cinema' => array(
            'label' => 'سينما سرد',
            'url' => 'https://sard360.com/cinema/',
            'categories' => array(
                array('name' => 'ذوات', 'url' => 'https://sard360.com/cinema/?category=' . rawurlencode('ذوات')),
                array('name' => 'تاريخ وحضارات', 'url' => 'https://sard360.com/cinema/?category=' . rawurlencode('تاريخ وحضارات')),
                array('name' => 'أدب وقراءات', 'url' => 'https://sard360.com/cinema/?category=' . rawurlencode('أدب وقراءات')),
                array('name' => 'تحقيقات كبرى', 'url' => 'https://sard360.com/cinema/?category=' . rawurlencode('تحقيقات كبرى')),
                array('name' => 'علوم وطبيعة', 'url' => 'https://sard360.com/cinema/?category=' . rawurlencode('علوم وطبيعة')),
                array('name' => 'أجواء وموسيقى', 'url' => 'https://sard360.com/cinema/?category=' . rawurlencode('أجواء وموسيقى')),
            ),
        ),
        'awraq' => array(
            'label' => 'أوراق سرد',
            'url' => 'https://sard360.com/awraq-sard/',
            'categories' => array(
                array('name' => 'آفاق', 'url' => 'https://sard360.com/cat-awraq/afaq/'),
                array('name' => 'الآثار والاكتشافات', 'url' => 'https://sard360.com/cat-awraq/athar/'),
                array('name' => 'الأدب والفنون', 'url' => 'https://sard360.com/cat-awraq/artsl/'),
                array('name' => 'التاريخ والوقائع', 'url' => 'https://sard360.com/cat-awraq/history/'),
                array('name' => 'الشعوب والأنثروبولوجيا', 'url' => 'https://sard360.com/cat-awraq/anthropology/'),
                array('name' => 'الفلسفة والفكر', 'url' => 'https://sard360.com/cat-awraq/philosophy/'),
                array('name' => 'الموسيقى والأنغام', 'url' => 'https://sard360.com/cat-awraq/musicology/'),
            ),
        ),
    );
    $encoded = wp_json_encode($navigation, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
    if (!$encoded) {
        return;
    }
    ?>
    <style id="sard360-footer-nav-style-v2">
      #footer-sard-root .footer-h4 a { color:inherit; text-decoration:none; }
      #footer-sard-root .footer-h4 a:hover,
      #footer-sard-root .footer-links a:hover { color:#d4a359; }
      #footer-sard-root .footer-h4 a:focus-visible,
      #footer-sard-root .footer-links a:focus-visible { outline:2px solid #d4a359; outline-offset:4px; border-radius:3px; }
    </style>
    <script id="sard360-footer-nav-v2">
    (()=>{
      const navigation=<?php echo $encoded; ?>;
      const renderFooter=()=>{
        const root=document.getElementById('footer-sard-root');
        if(!root)return false;
        const headings=Array.from(root.querySelectorAll('.footer-h4'));
        Object.values(navigation).forEach(section=>{
          const heading=headings.find(node=>(node.textContent||'').trim().includes(section.label));
          if(!heading)return;
          const col=heading.parentElement;
          if(heading){
            let link=heading.querySelector('a');
            if(!link){link=document.createElement('a');link.className='footer-section-link';heading.replaceChildren(link);}
            link.href=section.url;link.textContent=section.label;link.setAttribute('aria-label','افتح قسم '+section.label);
          }
          const list=col.querySelector('.footer-links');
          if(list){
            list.replaceChildren(...section.categories.map(item=>{
              const li=document.createElement('li'),a=document.createElement('a');
              a.href=item.url;a.textContent=item.name;
              if(section===navigation.cinema)a.setAttribute('data-sard-cinema-category',item.name);
              li.appendChild(a);return li;
            }));
          }
        });
        return true;
      };
      const routeCinemaCategory=()=>{
        const path=location.pathname.replace(/\/+$/,'')||'/';
        if(path!=='/cinema')return;
        const category=new URLSearchParams(location.search).get('category');
        if(!category)return;
        let tries=0,done=false;
        const stop=()=>{if(done)return;done=true;clearInterval(timer);observer.disconnect();};
        const clickFilter=()=>{
          if(done)return;
          const buttons=Array.from(document.querySelectorAll('.filter-button[data-category]'));
          const match=buttons.find(button=>button.dataset.category===category);
          if(match){if(match.getAttribute('aria-pressed')!=='true')match.click();stop();}
          else if(++tries>70)stop();
        };
        const observer=new MutationObserver(clickFilter);
        observer.observe(document.documentElement,{subtree:true,childList:true});
        const timer=setInterval(clickFilter,180);
        clickFilter();
      };
      const boot=()=>{renderFooter();routeCinemaCategory();};
      if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
      else boot();
      let retries=0;const retry=setInterval(()=>{if(renderFooter()||++retries>30)clearInterval(retry);},200);
    })();
    </script>
    <?php
}, 99);
