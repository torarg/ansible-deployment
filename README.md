
<!DOCTYPE html>

<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ansible_deployment.cli &#8212; ansible_deployment 0.0.1 documentation</title>
    <link rel="stylesheet" href="_static/flasky.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script src="_static/jquery.js"></script>
    <script src="_static/underscore.js"></script>
    <script src="_static/doctools.js"></script>
    <script src="_static/language_data.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />
    <link rel="next" title="ansible_deployment.cli_helpers" href="cli_helpers.html" />
    <link rel="prev" title="ansible_deployment.inventory_plugins" href="inventory_plugins.html" />
     
    
    <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9">

  </head><body>
    
    

    <div class="related" role="navigation" aria-label="related navigation">
      <h3>Navigation</h3>
      <ul>
        <li class="right" style="margin-right: 10px">
          <a href="genindex.html" title="General Index"
             accesskey="I">index</a></li>
        <li class="right" >
          <a href="py-modindex.html" title="Python Module Index"
             >modules</a> |</li>
        <li class="right" >
          <a href="cli_helpers.html" title="ansible_deployment.cli_helpers"
             accesskey="N">next</a> |</li>
        <li class="right" >
          <a href="inventory_plugins.html" title="ansible_deployment.inventory_plugins"
             accesskey="P">previous</a> |</li>
        <li class="nav-item nav-item-0"><a href="index.html">ansible_deployment 0.0.1 documentation</a> &#187;</li>
        <li class="nav-item nav-item-this"><a href="">ansible_deployment.cli</a></li> 
      </ul>
    </div>  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          <div class="body" role="main">
            
  <div class="section" id="ansible-deployment-cli">
<h1>ansible_deployment.cli<a class="headerlink" href="#ansible-deployment-cli" title="Permalink to this headline">¶</a></h1>
<div class="section" id="ansible-deployment">
<h2>ansible-deployment<a class="headerlink" href="#ansible-deployment" title="Permalink to this headline">¶</a></h2>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment <span class="o">[</span>OPTIONS<span class="o">]</span> COMMAND <span class="o">[</span>ARGS<span class="o">]</span>...
</pre></div>
</div>
<p class="rubric">Options</p>
<dl class="std option">
<dt id="cmdoption-ansible-deployment-version">
<code class="sig-name descname">--version</code><code class="sig-prename descclassname"></code><a class="headerlink" href="#cmdoption-ansible-deployment-version" title="Permalink to this definition">¶</a></dt>
<dd><p>Show the version and exit.</p>
</dd></dl>

<div class="section" id="ansible-deployment-delete">
<h3>delete<a class="headerlink" href="#ansible-deployment-delete" title="Permalink to this headline">¶</a></h3>
<p>Delete deployment.</p>
<p>Deletes all created files and directories in deployment directory.</p>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment delete <span class="o">[</span>OPTIONS<span class="o">]</span>
</pre></div>
</div>
</div>
<div class="section" id="ansible-deployment-init">
<h3>init<a class="headerlink" href="#ansible-deployment-init" title="Permalink to this headline">¶</a></h3>
<p>Initialize deployment directory.</p>
<p>Initialization requires a ‘deployment.json’ file in the
current working directory.</p>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment init <span class="o">[</span>OPTIONS<span class="o">]</span>
</pre></div>
</div>
</div>
<div class="section" id="ansible-deployment-run">
<h3>run<a class="headerlink" href="#ansible-deployment-run" title="Permalink to this headline">¶</a></h3>
<p>Run deployment with ansible-playbook.</p>
<p>This will create a commit in the deployment repository
containing the executed command.</p>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment run <span class="o">[</span>OPTIONS<span class="o">]</span> <span class="o">[</span>ROLE<span class="o">]</span>...
</pre></div>
</div>
<p class="rubric">Arguments</p>
<dl class="std option">
<dt id="cmdoption-ansible-deployment-run-arg-ROLE">
<span id="cmdoption-ansible-deployment-run-arg-role"></span><code class="sig-name descname">ROLE</code><code class="sig-prename descclassname"></code><a class="headerlink" href="#cmdoption-ansible-deployment-run-arg-ROLE" title="Permalink to this definition">¶</a></dt>
<dd><p>Optional argument(s)</p>
</dd></dl>

</div>
<div class="section" id="ansible-deployment-show">
<h3>show<a class="headerlink" href="#ansible-deployment-show" title="Permalink to this headline">¶</a></h3>
<p>Show deployment information.</p>
<p>Deployment information may be filtered by specifying attribute(s).</p>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment show <span class="o">[</span>OPTIONS<span class="o">]</span> <span class="o">[</span>ATTRIBUTE<span class="o">]</span>...
</pre></div>
</div>
<p class="rubric">Arguments</p>
<dl class="std option">
<dt id="cmdoption-ansible-deployment-show-arg-ATTRIBUTE">
<span id="cmdoption-ansible-deployment-show-arg-attribute"></span><code class="sig-name descname">ATTRIBUTE</code><code class="sig-prename descclassname"></code><a class="headerlink" href="#cmdoption-ansible-deployment-show-arg-ATTRIBUTE" title="Permalink to this definition">¶</a></dt>
<dd><p>Optional argument(s)</p>
</dd></dl>

</div>
<div class="section" id="ansible-deployment-ssh">
<h3>ssh<a class="headerlink" href="#ansible-deployment-ssh" title="Permalink to this headline">¶</a></h3>
<p>Run ‘ssh’ command to connect to a inventory host.</p>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment ssh <span class="o">[</span>OPTIONS<span class="o">]</span> HOST
</pre></div>
</div>
<p class="rubric">Arguments</p>
<dl class="std option">
<dt id="cmdoption-ansible-deployment-ssh-arg-HOST">
<span id="cmdoption-ansible-deployment-ssh-arg-host"></span><code class="sig-name descname">HOST</code><code class="sig-prename descclassname"></code><a class="headerlink" href="#cmdoption-ansible-deployment-ssh-arg-HOST" title="Permalink to this definition">¶</a></dt>
<dd><p>Required argument</p>
</dd></dl>

</div>
<div class="section" id="ansible-deployment-update">
<h3>update<a class="headerlink" href="#ansible-deployment-update" title="Permalink to this headline">¶</a></h3>
<p>Updates all deployment files and directories.</p>
<p>This will pull new changes from the roles source repository and
update all deployment files accordingly.
All changes will be shown as diff and the user needs to decide a.
update strategy.</p>
<div class="highlight-shell notranslate"><div class="highlight"><pre><span></span>ansible-deployment update <span class="o">[</span>OPTIONS<span class="o">]</span>
</pre></div>
</div>
</div>
</div>
</div>


            <div class="clearer"></div>
          </div>
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
  <h3><a href="index.html">Table of Contents</a></h3>
  <ul>
<li><a class="reference internal" href="#">ansible_deployment.cli</a><ul>
<li><a class="reference internal" href="#ansible-deployment">ansible-deployment</a><ul>
<li><a class="reference internal" href="#ansible-deployment-delete">delete</a></li>
<li><a class="reference internal" href="#ansible-deployment-init">init</a></li>
<li><a class="reference internal" href="#ansible-deployment-run">run</a></li>
<li><a class="reference internal" href="#ansible-deployment-show">show</a></li>
<li><a class="reference internal" href="#ansible-deployment-ssh">ssh</a></li>
<li><a class="reference internal" href="#ansible-deployment-update">update</a></li>
</ul>
</li>
</ul>
</li>
</ul>
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
      <li>Previous: <a href="inventory_plugins.html" title="previous chapter">ansible_deployment.inventory_plugins</a></li>
      <li>Next: <a href="cli_helpers.html" title="next chapter">ansible_deployment.cli_helpers</a></li>
  </ul></li>
</ul>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="_sources/cli.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3 id="searchlabel">Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" aria-labelledby="searchlabel" />
      <input type="submit" value="Go" />
    </form>
    </div>
</div>
<script>$('#searchbox').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>


    
    <div class="footer" role="contentinfo">
        &#169; Copyright 2020, Michael Wilson.
      Created using <a href="https://www.sphinx-doc.org/">Sphinx</a> 3.2.1.
    </div>
    

  </body>
</html>