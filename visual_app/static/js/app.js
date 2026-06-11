var DbcTool = DbcTool || {};

DbcTool.App = (function() {
    function switchModule(name) {
        document.querySelectorAll('.navbar .tab').forEach(function(t) { t.classList.remove('active'); });
        var tab = document.querySelector('.navbar .tab[data-module="' + name + '"]');
        if (tab) tab.classList.add('active');
        document.querySelectorAll('.module').forEach(function(m) { m.classList.remove('active'); });
        var mod = document.getElementById('module-' + name);
        if (mod) mod.classList.add('active');
        DbcTool.clearAllMsgs();
    }

    function init() {
        fetch('/api/formats')
            .then(function(r) { return r.json(); })
            .then(function(d) {
                var fmtMap = d.import;
                DbcTool.Convert.init(fmtMap);

                var inS = document.getElementById('inFmtCvt');
                d.import.forEach(function(f) {
                    var o = document.createElement('option');
                    o.value = f.key;
                    o.textContent = f.label;
                    inS.appendChild(o);
                });

                var outS = document.getElementById('outFmtCvt');
                d.export.forEach(function(f) {
                    var o = document.createElement('option');
                    o.value = f.key;
                    o.textContent = f.label;
                    outS.appendChild(o);
                });
            });

        DbcTool.setupUpload('zoneCvt', 'fileInpCvt', DbcTool.Convert.fileInCvt);
        DbcTool.setupUpload('zoneCmp1', 'fileInpCmp1', DbcTool.Compare.fileInCmp1);
        DbcTool.setupUpload('zoneCmp2', 'fileInpCmp2', DbcTool.Compare.fileInCmp2);

        document.getElementById('outFmtCvt').addEventListener('change', DbcTool.Convert.updBtnCvt);

        DbcTool.Compare.init();

        window.switchModule = switchModule;
        window.doConvert = DbcTool.Convert.doConvert;
        window.doCompare = DbcTool.Compare.doCompare;
        window.toggleAdv = DbcTool.toggleAdv;
        window.toggleDiffOnly = DbcTool.Compare.toggleDiffOnly;
    }

    return {
        init: init,
        switchModule: switchModule
    };
})();

document.addEventListener('DOMContentLoaded', function() {
    DbcTool.App.init();
});
