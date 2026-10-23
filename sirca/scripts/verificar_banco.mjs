import {PGlite} from '@electric-sql/pglite';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
fs.mkdirSync(path.join(root,'banco/resultados'),{recursive:true});
fs.mkdirSync(path.join(root,'evidencias'),{recursive:true});
const db=new PGlite();
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const report={motor:(await db.query('SELECT version()')).rows[0].version,checks:[],resultados:{},sha256:{}};
for(const f of ['banco/01_criar_tabelas.sql','banco/02_carregar_dados.sql']) {
 const sql=read(f);await db.exec(sql);report.sha256[f]=crypto.createHash('sha256').update(sql).digest('hex');
}
async function check(name,sql,expected) {
 const rows=(await db.query(sql)).rows;
 const ok=JSON.stringify(rows)===JSON.stringify(expected);
 report.checks.push({teste:name,ok,resultado:rows});if(!ok)throw new Error(name+': '+JSON.stringify(rows));
}
const total=(await db.query("SELECT relname AS tabela,n_live_tup FROM pg_stat_user_tables ORDER BY relname")).rows;
report.contagens={};
for(const t of ['familia','participante','colaborador','oficina','encontro','frequencia','doacao','orgao','encaminhamento','lacuna_frequencia']) report.contagens[t]=(await db.query('SELECT COUNT(*)::integer AS n FROM '+t)).rows[0].n;
await check('FKs / orfaos',`SELECT COUNT(*)::integer AS n FROM frequencia f LEFT JOIN participante p USING(id_participante) LEFT JOIN oficina o USING(id_oficina) WHERE p.id_participante IS NULL OR o.id_oficina IS NULL`,[{n:0}]);
await check('RN-01 dominio',"SELECT COUNT(*)::integer AS n FROM frequencia WHERE presenca NOT IN('presente','falta','falta justificada')",[{n:0}]);
await check('RN-02 familia',"SELECT COUNT(*)::integer AS n FROM participante p LEFT JOIN familia f USING(id_familia) WHERE f.id_familia IS NULL",[{n:0}]);
await check('RN-03 duplicatas',"SELECT COUNT(*)::integer AS n FROM(SELECT 1 FROM frequencia GROUP BY id_participante,id_oficina,data_encontro HAVING COUNT(*)>1) x",[{n:0}]);
await check('RN-04 desligamento',"SELECT COUNT(*)::integer AS n FROM frequencia f JOIN participante p USING(id_participante) WHERE p.situacao='desligado' AND(p.data_desligamento IS NULL OR f.data_encontro>=p.data_desligamento)",[{n:0}]);
async function refused(name,sql,code) {
 await db.exec('BEGIN');let error=null;
 try {await db.exec(sql);}catch(e){error={code:e.code,mensagem:e.message};}
 await db.exec('ROLLBACK');
 const ok=error!==null && (!code||error.code===code);
 report.checks.push({teste:name,ok,erro:error});if(!ok)throw new Error(name+' deveria rejeitar por '+code);
}
const f=(await db.query('SELECT * FROM frequencia LIMIT 1')).rows[0];
const values=(p,o,d,s,who=f.id_registrador)=>`('${p}','${o}','${d}','${s}','${who}',CURRENT_TIMESTAMP,'sessao')`;
const cols='(id_participante,id_oficina,data_encontro,presenca,id_registrador,registrado_em,origem)';
const d=f.data_encontro.toISOString().slice(0,10);
await refused('RF-07 participante inexistente',`INSERT INTO frequencia ${cols} VALUES ${values('P999',f.id_oficina,d,'presente')}`,'23503');
await refused('RF-07 oficina inexistente',`INSERT INTO frequencia ${cols} VALUES ${values(f.id_participante,'OF99',d,'presente')}`,'23503');
await refused('RN-01 dominio invalido',`INSERT INTO frequencia ${cols} VALUES ${values(f.id_participante,f.id_oficina,d,'P')}`,'23514');
await refused('RN-03 repeticao',`INSERT INTO frequencia ${cols} VALUES ${values(f.id_participante,f.id_oficina,d,'presente')}`,'23505');
const deslig=(await db.query("SELECT id_participante FROM participante WHERE situacao='desligado' LIMIT 1")).rows[0].id_participante;
await refused('RN-04 desligado sem data',`INSERT INTO frequencia ${cols} VALUES ${values(deslig,f.id_oficina,d,'presente')}`,'P0001');
await refused('RN-04 alteracao cadastral contraditoria',`UPDATE participante SET situacao='desligado',data_desligamento=NULL WHERE id_participante='${f.id_participante}'`,'P0001');
// Limite exato de RN-04: antes do desligamento aceita; na data recusa.
await db.exec('BEGIN');
await db.exec("INSERT INTO participante VALUES('TESTE','Teste SQL','F001','2000-01-01',NULL,NULL,'2020-01-01','desligado','2025-01-02');INSERT INTO encontro VALUES('OF01','2025-01-01'),('OF01','2025-01-02')");
await db.exec(`INSERT INTO frequencia ${cols} VALUES ${values('TESTE','OF01','2025-01-01','presente')}`);
report.checks.push({teste:'RN-04 historico anterior ao desligamento aceita',ok:true});
await db.exec('SAVEPOINT data_limite');let boundary=false;
try {await db.exec(`INSERT INTO frequencia ${cols} VALUES ${values('TESTE','OF01','2025-01-02','presente')}`);}catch(e){boundary=e.code==='P0001';}
await db.exec('ROLLBACK TO SAVEPOINT data_limite');await db.exec('ROLLBACK');
report.checks.push({teste:'RN-04 data igual ao desligamento recusa',ok:boundary});if(!boundary)throw new Error('Limite RN-04');
for(const pn of ['PN-01','PN-02','PN-03','PN-04','PN-05']) {
 const sql=read('banco/consultas/'+pn+'.sql');const rows=(await db.query(sql)).rows;report.resultados[pn]=rows;
 fs.writeFileSync(path.join(root,'banco/resultados',pn+'.json'),JSON.stringify(rows,null,2));
 const fields=rows.length?Object.keys(rows[0]):(pn==='PN-03'?['id_participante','id_oficina','primeira_falta','ultima_falta','encontros_consecutivos']:[]);
 const q=v=>v===null?'':`"${(v instanceof Date?v.toISOString():String(v)).replaceAll('"','""')}"`;
 fs.writeFileSync(path.join(root,'banco/resultados',pn+'.csv'),[fields.join(','),...rows.map(r=>fields.map(k=>q(r[k])).join(','))].join('\n')+'\n');
}
// Massa controlada isola a semantica de PN-03, sem alterar a base final.
await db.exec('BEGIN');
await db.exec("DELETE FROM frequencia;DELETE FROM encontro;DELETE FROM lacuna_frequencia;");
await db.exec("INSERT INTO participante VALUES('TESTE','Teste SQL','F001','2000-01-01',NULL,NULL,'2020-01-01','ativo',NULL)");
for(let i=1;i<=4;i++)await db.exec(`INSERT INTO encontro VALUES('OF01','2025-07-0${i}')`);
for(let i=1;i<=3;i++)await db.exec(`INSERT INTO frequencia ${cols} VALUES ${values('TESTE','OF01','2025-07-0'+i,'falta')}`);
const pn3=read('banco/consultas/PN-03.sql');
let rows=(await db.query(pn3)).rows;let ok=rows.length===1&&rows[0].encontros_consecutivos===3;
report.checks.push({teste:'PN-03 tres faltas consecutivas detectadas',ok});if(!ok)throw new Error('PN3 positivo');
await db.exec("DELETE FROM frequencia WHERE data_encontro='2025-07-02'");
rows=(await db.query(pn3)).rows;ok=rows.length===0;
report.checks.push({teste:'PN-03 lacuna de registro interrompe sequencia',ok});if(!ok)throw new Error('PN3 lacuna');
await db.exec(`INSERT INTO frequencia ${cols} VALUES ${values('TESTE','OF01','2025-07-02','falta justificada')}`);
rows=(await db.query(pn3)).rows;ok=rows.length===0;
report.checks.push({teste:'PN-03 justificada interrompe sequencia',ok});if(!ok)throw new Error('PN3 justificada');
await db.exec("UPDATE frequencia SET presenca='falta' WHERE data_encontro='2025-07-02';INSERT INTO lacuna_frequencia VALUES(999,'OF01','2025-07-02','2025-07-02','Teste de cobertura')");
rows=(await db.query(pn3)).rows;ok=rows.length===0;
report.checks.push({teste:'PN-03 caderno perdido impede conclusao',ok});if(!ok)throw new Error('PN3 cobertura');
await db.exec('ROLLBACK');
fs.writeFileSync(path.join(root,'evidencias/banco.json'),JSON.stringify(report,null,2));
await db.close();
console.log(JSON.stringify({motor:report.motor,contagens:report.contagens,testes:report.checks.length,todos_aprovados:report.checks.every(x=>x.ok),resultados:report.resultados},null,2));
