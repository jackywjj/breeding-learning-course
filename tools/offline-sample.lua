-- Normalize chapter links and Mermaid images in single-document formats.
local offline = FORMAT == "typst" or FORMAT:match("^epub")

function Link(link)
  if not offline then
    return
  end

  local chapter, anchor = link.target:match("^([%w%-]+)%.qmd(.*)$")
  if chapter then
    link.target = anchor ~= "" and anchor or "#" .. chapter
    return link
  end
end

function Para(para)
  -- Keep a chapter opener with its first paragraph even when navigation follows the heading.
  if FORMAT == "typst" and pandoc.utils.stringify(para):match("^目录 / Contents%s*·") then
    return {
      pandoc.RawBlock("typst", '#block(sticky: true, below: 0.8em)[#set text(size: 9pt, fill: rgb("#705858"))'),
      para,
      pandoc.RawBlock("typst", "]"),
    }
  end
end

function Div(div)
  if not offline or not div.classes:includes("cell") then
    return
  end

  local diagram
  div:walk({
    Image = function(img)
      if img.src:match("mermaid%-figure%-.*%.png$") then
        diagram = img
      end
    end,
  })
  if diagram then
    diagram.attributes.width = "100%"
    diagram.attributes.height = nil
    diagram.caption = pandoc.Inlines("本节示意图 / Section diagram")
    return pandoc.Para({diagram})
  end
end
