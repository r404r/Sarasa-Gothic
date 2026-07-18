#!/usr/bin/env node
// CI 用：把 config.json 收窄到「单 region × 单权重组」，以便每个 matrix job 只做一个权重的 CJK hinting，
// 从而单 job 稳落在 GitHub Actions 6h/job 上限内（本机 16 线程 SC+J 全量冷构建 5h32m 为据）。
// 确定性生成、不手工编辑；保持 styles/uprightStyleMap 引用完整。
// 用法: node ci/gen-config.mjs <region: sc|j> <weightgroup: regular|bold>
import fs from "node:fs";

const REGION = { sc: "SC", j: "J" };
const WG = {
	regular: ["Regular", "Italic"],
	bold: ["Bold", "BoldItalic"],
};

const [, , regionArg, wgArg] = process.argv;
if (!REGION[regionArg] || !WG[wgArg]) {
	console.error("usage: node ci/gen-config.mjs <sc|j> <regular|bold>");
	process.exit(2);
}
const region = REGION[regionArg];
const styles = WG[wgArg];

const p = "config.json";
const cfg = JSON.parse(fs.readFileSync(p, "utf8"));

// region：只留一个（subfamilyOrder 是 region 枚举入口，Phase 0 已确认）
cfg.subfamilyOrder = [region];
// style：只留该权重组两项
cfg.styleOrder = styles.filter((s) => cfg.styleOrder.includes(s));
// styles 键同步收窄（verdafile.mjs:591 按 config.styles 键迭代）；保留组内 uprightStyleMap 目标
const keep = new Set(cfg.styleOrder);
for (const s of cfg.styleOrder) {
	const up = cfg.styles[s]?.uprightStyleMap;
	if (up) keep.add(up);
}
cfg.styles = Object.fromEntries(Object.entries(cfg.styles).filter(([k]) => keep.has(k)));

// 引用完整性自检
for (const s of cfg.styleOrder) {
	if (!cfg.styles[s]) {
		console.error(`FATAL: styleOrder ${s} 不在 styles`);
		process.exit(1);
	}
	const up = cfg.styles[s].uprightStyleMap;
	if (up && !cfg.styles[up]) {
		console.error(`FATAL: styles.${s}.uprightStyleMap ${up} 缺失`);
		process.exit(1);
	}
}

fs.writeFileSync(p, `${JSON.stringify(cfg, null, "\t")}\n`);
const n = cfg.familyOrder.length * cfg.subfamilyOrder.length * cfg.styleOrder.length;
console.log(
	`gen-config: region=${region} weightgroup=${wgArg} ` +
		`familyOrder=${JSON.stringify(cfg.familyOrder)} ` +
		`subfamilyOrder=${JSON.stringify(cfg.subfamilyOrder)} ` +
		`styleOrder=${JSON.stringify(cfg.styleOrder)} ` +
		`-> ${n} Prod (out/TTF ${n} + out/TTF-Unhinted ${n} = ${n * 2} TTF)`,
);
