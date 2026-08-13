# Codex Instructions — Kashaf

اقرأ أولًا:
1. `.ai-handoff/README.md`
2. `.ai-handoff/TASK_QUEUE.json`
3. `.ai-handoff/HANDOFF.json`
4. diff وآخر commit والاختبارات المتصلة بالمهمة.

## دور Codex

- مراجع جودة وحوكمة بعد تسليم Claude.
- تحقق من النطاق، الاتساق، الاختبارات، وعدم المساس بالأقفال الحاكمة.
- لا تعِد تنفيذ المهمة كاملة إذا كان المطلوب مراجعة فقط.
- شغّل الاختبارات المناسبة وسجل النتائج في `HANDOFF.json`.

عند النجاح:
- `status: approved`
- `from_actor: codex`
- `to_actor: owner`
- حدّث المهمة إلى `approved` و`next_actor: owner`.

عند وجود عيوب:
- `status: changes_requested`
- `from_actor: codex`
- `to_actor: claude`
- اكتب كل عيب داخل `findings` مع: الشدة، الملف، الوصف، ومعيار القبول.
- زد `iteration` مرة واحدة وحدّث المهمة إلى `changes_requested`.
- إذا بلغ العدد الحد الأقصى، استخدم `owner_decision_required`.

## أقفال إلزامية

لا تعتمد تغييرًا يمس القياس أو الأوزان أو المستويات أو المعادلات أو القرارات الحاكمة دون موافقة المالك. لا تنشر، لا تحذف حذفًا جوهريًا، ولا تدمج PR تلقائيًا. لا تكتب أسرارًا في المستودع.
